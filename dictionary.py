"""
Dictionary API integration module for QuickMeaning.
Supports English and foreign language lookups via Wiktionary API.
Supports smart headword extraction, titlecase fallback, and entry relevancy scoring.
"""

import re
import html
import json
import urllib.request
import urllib.error
import urllib.parse
import socket
from dataclasses import dataclass
from typing import Optional

from config import (
    WIKTIONARY_API_URL,
    REQUEST_TIMEOUT,
    USER_AGENT
)


@dataclass
class LookupResult:
    word: str
    language: Optional[str] = None
    part_of_speech: Optional[str] = None
    definition: Optional[str] = None
    pronunciation: Optional[str] = None
    error_message: Optional[str] = None


class DictionaryService:
    def __init__(self):
        self.headers = {"User-Agent": USER_AGENT}

    def _clean_html(self, text: str) -> str:
        """Strip HTML tags and unescape HTML entities from definitions."""
        if not text:
            return ""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = html.unescape(clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    def _is_grammatical_inflection(self, def_str: str) -> bool:
        """Check if definition is an obscure grammatical inflection rather than a primary meaning."""
        d = def_str.lower().strip()
        patterns = [
            r'^plural of\b', r'^feminine of\b', r'^masculine of\b',
            r'^participle of\b', r'^inflection of\b', r'^past tense of\b',
            r'^second-person\b', r'^third-person\b', r'^alternative spelling of\b',
            r'^alternative form of\b', r'^misspelling of\b'
        ]
        return any(re.search(p, d) for p in patterns)

    def _score_definition(self, lang_code: str, pos: str, def_clean: str) -> int:
        """
        Score a candidate definition to prefer primary/common meanings over obscure grammatical entries.
        """
        score = 100
        d_lower = def_clean.lower().strip()

        # Prefer English definitions for general lookup
        if lang_code == 'en':
            score += 50

        # Penalize obscure grammatical inflections (e.g. 'plural of pari')
        if self._is_grammatical_inflection(def_clean):
            score -= 80

        # Penalize obscure taxonomic genus entries if possible
        if d_lower.startswith('a taxonomic genus') or d_lower.startswith('a taxonomic species'):
            score -= 40

        # Bonus for key high-value indicators
        if any(kw in d_lower for kw in ['capital', 'city', 'greeting', 'salutation', 'discovery', 'good morning', 'thank you']):
            score += 30

        return score

    def _get_query_candidates(self, word: str) -> list[str]:
        """
        Generate candidate queries in priority order:
        1. Exact query
        2. Titlecase (e.g. 'paris' -> 'Paris')
        3. Lowercase (if user typed uppercase)
        4. Article / headword stripped (e.g. 'La fille' -> 'fille', 'L\'eau' -> 'eau')
        5. Phrasal term space substitution ('pop up' -> 'pop-up')
        """
        clean = word.strip()
        candidates = [clean]

        # Titlecase variant (e.g. paris -> Paris)
        title_var = clean.title()
        if title_var not in candidates:
            candidates.append(title_var)

        # Lowercase variant
        lower_var = clean.lower()
        if lower_var not in candidates:
            candidates.append(lower_var)

        # Apostrophe article removal (e.g. L'eau -> eau, l'arbre -> arbre)
        if re.match(r"^[a-zA-Z]['’]", clean):
            stripped_apos = re.sub(r"^[a-zA-Z]['’]\s*", "", clean)
            if stripped_apos and stripped_apos not in candidates:
                candidates.append(stripped_apos)

        # Leading article removal
        articles = [
            "la ", "le ", "les ", "un ", "une ", "des ",
            "el ", "los ", "las ", "una ", "unos ", "unas ",
            "der ", "die ", "das ", "ein ", "eine ", "einen ", "einem ", "eines ", "einer ",
            "the ", "a ", "an ",
            "il ", "lo ", "os ", "as "
        ]
        for art in articles:
            if lower_var.startswith(art):
                stripped = clean[len(art):].strip()
                if stripped and stripped not in candidates:
                    candidates.append(stripped)
                break

        # Phrasal term hyphenation/joining (e.g. pop up -> pop-up, popup)
        if " " in clean:
            hyphenated = clean.replace(" ", "-")
            if hyphenated not in candidates:
                candidates.append(hyphenated)
            joined = clean.replace(" ", "")
            if joined not in candidates:
                candidates.append(joined)

        return candidates

    def lookup(self, word: str) -> LookupResult:
        """
        Perform dictionary lookup for a given word or phrase.
        Evaluates and scores candidate queries and definitions to return the most relevant result.
        Preserves original user query in returned LookupResult.
        """
        clean_word = word.strip()
        if not clean_word:
            return LookupResult(word=word, error_message="Word not found.")

        query_candidates = self._get_query_candidates(clean_word)
        all_definitions = []

        try:
            for q in query_candidates:
                url = f"{WIKTIONARY_API_URL}{urllib.parse.quote(q)}"
                req = urllib.request.Request(url, headers=self.headers)

                try:
                    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        if not isinstance(data, dict) or not data:
                            continue

                        for lang_code, entries in data.items():
                            if not isinstance(entries, list):
                                continue
                            for entry in entries:
                                lang_name = entry.get('language', lang_code.upper())
                                pos = entry.get('partOfSpeech', '')
                                raw_defs = entry.get('definitions', [])

                                for d in raw_defs:
                                    if isinstance(d, dict) and 'definition' in d:
                                        c_def = self._clean_html(d['definition'])
                                        if c_def:
                                            sc = self._score_definition(lang_code, pos, c_def)
                                            all_definitions.append({
                                                'query': q,
                                                'lang_code': lang_code,
                                                'language': lang_name,
                                                'part_of_speech': pos.lower() if pos else None,
                                                'definition': c_def,
                                                'score': sc
                                            })
                except Exception:
                    pass

                # If we found strong definitions (score >= 120) for early candidates, stop querying
                if any(d['score'] >= 120 for d in all_definitions):
                    break

            if not all_definitions:
                return LookupResult(word=clean_word, error_message="Word not found.")

            # Sort definitions by score (highest relevancy first)
            all_definitions.sort(key=lambda x: x['score'], reverse=True)
            best = all_definitions[0]

            # Format primary definition
            primary_def = best['definition']
            
            # If second definition exists for same language and has decent score, include bullet point
            same_lang_defs = [d for d in all_definitions if d['language'] == best['language'] and d['definition'] != primary_def]
            if same_lang_defs and len(primary_def) < 70 and not self._is_grammatical_inflection(same_lang_defs[0]['definition']):
                primary_def = f"{primary_def}\n• {same_lang_defs[0]['definition']}"

            return LookupResult(
                word=clean_word,  # Preserve user's original query in UI
                language=best['language'],
                part_of_speech=best['part_of_speech'],
                definition=primary_def
            )

        except urllib.error.URLError as e:
            if isinstance(e.reason, socket.timeout):
                return LookupResult(word=clean_word, error_message="The lookup timed out. Try again.")
            return LookupResult(word=clean_word, error_message="Unable to connect. Check your internet connection.")

        except (TimeoutError, socket.timeout):
            return LookupResult(word=clean_word, error_message="The lookup timed out. Try again.")

        except Exception:
            return LookupResult(word=clean_word, error_message="No definition available.")

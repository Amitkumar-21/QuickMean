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
    FREE_DICTIONARY_API_URL,
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

    def _score_definition(self, lang_name: str, pos: str, def_clean: str, is_exact_query: bool = True) -> int:
        """
        Score candidate definitions according to strict language and relevancy priority:
        1. Exact English entry / common English definition (+100)
        2. Exact requested foreign-language entry / modern living language (+40)
        3. Archaic or historical language entries (-20)
        4. Translingual / ISO code / symbol / rare entries as fallback (-120)
        """
        score = 100
        lang_lower = (lang_name or '').lower().strip()
        d_lower = def_clean.lower().strip()
        pos_lower = (pos or '').lower().strip()

        # Language priority ranking
        if lang_lower == 'english':
            score += 100
        elif lang_lower in ['translingual', 'symbol']:
            score -= 120
        elif any(archaic in lang_lower for archaic in ['middle english', 'old english', 'old norse', 'old french', 'proto-']):
            score -= 20
        else:
            score += 40

        # Heavy penalty for technical symbols / ISO language codes / taxonomic specs
        if re.search(r'iso 639|\blanguage code\b|\bchemical symbol\b|\bmath symbol\b|\btaxonomic genus\b|\btaxonomic species\b', d_lower):
            score -= 100

        # Penalize obscure grammatical inflections (e.g. 'plural of pari')
        if self._is_grammatical_inflection(def_clean):
            score -= 60

        # Penalize symbol/character parts of speech
        if pos_lower in ['symbol', 'letter', 'character']:
            score -= 40

        # Bonus for key high-value human meaning indicators
        if any(kw in d_lower for kw in ['greeting', 'salutation', 'discovery', 'good day', 'thank you', 'girl', 'boy', 'waiter', 'misfortune', 'pleasure', 'capital', 'city']):
            score += 30

        if is_exact_query:
            score += 20

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

    def _lookup_free_dictionary(self, word: str) -> Optional[LookupResult]:
        """Attempt primary lookup via Free Dictionary API for single-word English terms and phonetics."""
        clean = word.strip()
        if not clean or ' ' in clean:
            return None

        url = f"{FREE_DICTIONARY_API_URL}{urllib.parse.quote(clean.lower())}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if isinstance(data, list) and len(data) > 0:
                    entry = data[0]
                    meanings = entry.get('meanings', [])
                    if not meanings:
                        return None

                    # Extract pronunciation/phonetics
                    phonetic = entry.get('phonetic', '')
                    if not phonetic:
                        for p in entry.get('phonetics', []):
                            if isinstance(p, dict) and p.get('text'):
                                phonetic = p.get('text')
                                break

                    primary_pos = None
                    primary_def = None
                    secondary_def = None

                    for m in meanings:
                        pos = m.get('partOfSpeech')
                        defs = m.get('definitions', [])
                        for d in defs:
                            d_text = self._clean_html(d.get('definition', ''))
                            if d_text and not self._is_grammatical_inflection(d_text):
                                if not primary_def:
                                    primary_pos = pos
                                    primary_def = d_text
                                elif not secondary_def and pos == primary_pos:
                                    secondary_def = d_text
                                    break
                        if primary_def and secondary_def:
                            break

                    if primary_def:
                        full_def = primary_def
                        if secondary_def and len(primary_def) < 70:
                            full_def = f"{primary_def}\n• {secondary_def}"
                        return LookupResult(
                            word=clean,
                            language="English",
                            part_of_speech=primary_pos.lower() if primary_pos else None,
                            definition=full_def,
                            pronunciation=phonetic if phonetic else None
                        )
        except Exception:
            pass
        return None

    def _lookup_wiktionary(self, word: str) -> LookupResult:
        """Multilingual lookup and fallback engine using Wiktionary API."""
        clean_word = word.strip()
        query_candidates = self._get_query_candidates(clean_word)
        all_definitions = []

        for idx, q in enumerate(query_candidates):
            url = f"{WIKTIONARY_API_URL}{urllib.parse.quote(q)}"
            req = urllib.request.Request(url, headers=self.headers)

            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if not isinstance(data, dict) or not data:
                        continue

                    is_exact = (idx == 0)
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
                                        sc = self._score_definition(lang_name, pos, c_def, is_exact_query=is_exact)
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

            # Only break early if a very high relevancy definition is found for exact query
            if any(d['score'] >= 180 for d in all_definitions):
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

    def lookup(self, word: str) -> LookupResult:
        """
        Perform dictionary lookup for a given word or phrase.
        First attempts Free Dictionary API for English lookups and phonetics.
        Falls back to Wiktionary API for multilingual support and robust entry selection.
        """
        clean_word = word.strip()
        if not clean_word:
            return LookupResult(word=word, error_message="Word not found.")

        # Try Free Dictionary API first for single-word English entries
        res = self._lookup_free_dictionary(clean_word)
        if res:
            return res

        # Multilingual & fallback engine via Wiktionary API
        return self._lookup_wiktionary(clean_word)

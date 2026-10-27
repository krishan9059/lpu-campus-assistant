from app.services.language import detect_language, resolve_language


def test_detects_english():
    assert detect_language("What time does the library open?") == "en"


def test_detects_hindi():
    assert detect_language("पुस्तकालय कब खुलता है?") == "hi"


def test_detects_punjabi():
    assert detect_language("ਲਾਇਬ੍ਰੇਰੀ ਕਦੋਂ ਖੁੱਲ੍ਹਦੀ ਹੈ?") == "pa"


def test_mixed_script_majority_wins():
    assert detect_language("Library ਲਾਇਬ੍ਰੇਰੀ ਸਮਾਂ ਕੀ ਹੈ") == "pa"


def test_short_romanised_hindi_is_treated_as_english():
    assert detect_language("library kab khulti hai") == "en"


def test_resolve_language_respects_explicit_choice():
    assert resolve_language("hi", "what time is the library open") == "hi"


def test_resolve_language_auto_detects():
    assert resolve_language("auto", "पुस्तकालय कब खुलता है?") == "hi"

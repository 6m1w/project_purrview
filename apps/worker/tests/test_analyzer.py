"""Tests for analyzer module."""

from src.analyzer import (
    Activity,
    CatActivity,
    IdentifyResult,
    CAT_NAMES,
    CAT_DESCRIPTIONS,
)


class TestSchema:
    def test_activity_enum_values(self):
        assert Activity.EATING.value == "eating"
        assert Activity.DRINKING.value == "drinking"
        assert Activity.PRESENT.value == "present"

    def test_cat_activity_model(self):
        ca = CatActivity(name="大吉", activity=Activity.EATING)
        assert ca.name == "大吉"
        assert ca.activity == Activity.EATING

    def test_identify_result_from_json(self):
        data = {
            "cats_present": True,
            "cats": [{"name": "大吉", "activity": "eating"}],
            "description": "test",
            "confidence": 0.95,
        }
        result = IdentifyResult.model_validate(data)
        assert result.cats_present is True
        assert len(result.cats) == 1
        assert result.cats[0].name == "大吉"
        assert result.cats[0].activity == Activity.EATING

    def test_identify_result_empty_cats(self):
        result = IdentifyResult(cats_present=False, confidence=0.0)
        assert result.cats == []

    def test_cat_names_has_five_cats(self):
        assert len(CAT_NAMES) == 5

    def test_cat_descriptions_match_names(self):
        for name in CAT_NAMES:
            assert name in CAT_DESCRIPTIONS

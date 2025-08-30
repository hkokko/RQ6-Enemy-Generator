import re
import os
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from enemygen.models import EnemyTemplate, Race, Ruleset

pytestmark = pytest.mark.skipif(os.environ.get("ALLOW_UI_DB_TESTS") != "1", reason="UI tests require a live DB (MySQL). Set ALLOW_UI_DB_TESTS=1 to enable.")


def _db_guard():
    try:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception as e:
        pytest.skip(f"Database not reachable for UI tests: {type(e).__name__}: {e}")


def _setup_env(client):
    """Create or update user, login, create ruleset, race, and base template. Return (client, user, rs, race, et)."""
    _db_guard()
    user, _ = User.objects.get_or_create(username="tester", defaults={"is_active": True})
    user.set_password("pw12345")
    user.save(update_fields=["password"])  # keep idempotent
    client.login(username="tester", password="pw12345")

    rs = Ruleset.objects.create(name="RQ6", owner=user)
    race = Race.create(owner=user, name="Human")
    rs.races.add(race)
    # Attach available skills to the ruleset so EnemyTemplate will have standard skills
    try:
        from enemygen.models import SkillAbstract
        skills = list(SkillAbstract.objects.all())
        if skills:
            rs.skills.add(*skills)
    except Exception:
        # If SkillAbstract isn't available for any reason, continue; tests that depend on it may skip
        pass
    rs.save()

    et = EnemyTemplate.create(owner=user, ruleset=rs, race=race, name="Base Template")
    return client, user, rs, race, et


def _clone(client, et_id):
    resp = client.post(reverse('clone_template', args=[et_id]))
    # Parse new id regardless of assertions; tests will assert response as needed
    new_id = None
    try:
        if 'Location' in resp:
            m = re.search(r"/enemy_template/(\d+)/", resp['Location'])
            if m:
                new_id = int(m.group(1))
    except Exception:
        pass
    return resp, new_id


# ---------------------- HTTP status tests (one assert each) ----------------------

@pytest.mark.django_db(transaction=True)
def test_get_enemy_template_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp = c.get(reverse('enemy_template', args=[et.id]))
    assert resp.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_clone_redirects_302(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, _new_id = _clone(c, et.id)
    assert resp.status_code == 302


@pytest.mark.django_db(transaction=True)
def test_new_template_page_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    # Follow to new page
    follow = c.get(resp['Location']) if 'Location' in resp else None
    assert (follow is not None) and (follow.status_code == 200)


@pytest.mark.django_db(transaction=True)
def test_submit_published_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    r = c.post(reverse('submit', args=[new_id]), data={'object': 'et_published', 'value': 'true', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_cult_rank_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    r = c.post(reverse('submit', args=[new_id]), data={'object': 'et_cult_rank', 'value': '2', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_movement_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    r = c.post(reverse('submit', args=[new_id]), data={'object': 'et_movement', 'value': '10', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_natural_armor_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    r = c.post(reverse('submit', args=[new_id]), data={'object': 'et_natural_armor', 'value': 'true', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_home_200(client):
    c, _u, _rs, _race, et = _setup_env(client)
    # home does not depend on a specific ET; ensure reachable
    home = c.get(reverse('home'))
    assert home.status_code == 200


# -------- Optional data-dependent submit tests (skip if data not present) --------

@pytest.mark.django_db(transaction=True)
def test_submit_first_skill_include_200(client):
    from enemygen.models import EnemySkill
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    es = EnemySkill.objects.filter(enemy_template_id=new_id).first()
    if not es:
        pytest.skip("No EnemySkill found for cloned template")
    r = c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_include', 'value': 'true', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_first_skill_value_200(client):
    from enemygen.models import EnemySkill
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    es = EnemySkill.objects.filter(enemy_template_id=new_id).first()
    if not es:
        pytest.skip("No EnemySkill found for cloned template")
    r = c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_value', 'value': '11', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_hit_location_armor_200(client):
    from enemygen.models import EnemyHitLocation
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    ehl = EnemyHitLocation.objects.filter(enemy_template_id=new_id).first()
    if not ehl:
        pytest.skip("No EnemyHitLocation found for cloned template")
    r = c.post(reverse('submit', args=[ehl.id]), data={'object': 'et_hl_armor', 'value': '12', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_submit_feature_prob_200(client):
    from enemygen.models import AdditionalFeatureList, EnemyAdditionalFeatureList
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    afl = AdditionalFeatureList.objects.first()
    if not afl:
        pytest.skip("No AdditionalFeatureList available")
    new_et = EnemyTemplate.objects.get(id=new_id)
    eafl = EnemyAdditionalFeatureList.create(new_et, afl.id)
    r = c.post(reverse('submit', args=[eafl.id]), data={'object': 'et_feature_prob', 'value': '13', 'parent_id': None}, content_type='application/json')
    assert r.status_code == 200


# --------------------------- DB state verification tests ---------------------------

@pytest.mark.django_db(transaction=True)
def test_db_published_true(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    # Set value (no assert here); this test's single assert is the DB check
    c.post(reverse('submit', args=[new_id]), data={'object': 'et_published', 'value': 'true', 'parent_id': None}, content_type='application/json')
    new_et = EnemyTemplate.objects.get(id=new_id)
    assert new_et.published is True


@pytest.mark.django_db(transaction=True)
def test_db_movement_10(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    c.post(reverse('submit', args=[new_id]), data={'object': 'et_movement', 'value': '10', 'parent_id': None}, content_type='application/json')
    new_et = EnemyTemplate.objects.get(id=new_id)
    assert str(new_et.movement) == '10'


@pytest.mark.django_db(transaction=True)
def test_db_natural_armor_true(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    c.post(reverse('submit', args=[new_id]), data={'object': 'et_natural_armor', 'value': 'true', 'parent_id': None}, content_type='application/json')
    new_et = EnemyTemplate.objects.get(id=new_id)
    assert new_et.natural_armor is True


@pytest.mark.django_db(transaction=True)
def test_db_cult_rank_2(client):
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    c.post(reverse('submit', args=[new_id]), data={'object': 'et_cult_rank', 'value': '2', 'parent_id': None}, content_type='application/json')
    new_et = EnemyTemplate.objects.get(id=new_id)
    assert int(new_et.cult_rank) == 2


@pytest.mark.django_db(transaction=True)
def test_db_hit_location_armor_12(client):
    from enemygen.models import EnemyHitLocation
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    ehl = EnemyHitLocation.objects.filter(enemy_template_id=new_id).first()
    if not ehl:
        pytest.skip("No EnemyHitLocation found for cloned template")
    c.post(reverse('submit', args=[ehl.id]), data={'object': 'et_hl_armor', 'value': '12', 'parent_id': None}, content_type='application/json')
    ehl_ref = EnemyHitLocation.objects.get(id=ehl.id)
    assert str(ehl_ref.armor) == '12'


@pytest.mark.django_db(transaction=True)
def test_db_skill_updates(client):
    from enemygen.models import EnemySkill
    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)
    es = EnemySkill.objects.filter(enemy_template_id=new_id).first()
    if not es:
        pytest.skip("No EnemySkill found for cloned template")
    # Set include and value; assert only the final expected value
    c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_include', 'value': 'true', 'parent_id': None}, content_type='application/json')
    c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_value', 'value': '11', 'parent_id': None}, content_type='application/json')
    es_ref = EnemySkill.objects.get(id=es.id)
    assert (es_ref.include is True) and (str(es_ref.die_set) == '11')


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "skill_name",
    [
        "Athletics",
        "Boating",
        "Brawn",
        "Conceal",
        "Customs",
        "Dance",
        "Deceit",
        "Drive",
        "Endurance",
        "Evade",
        "Influence",
        "Insight",
        "Locale",
        "Perception",
        "Ride",
        "Sing",
        "Sleight",
        "Stealth",
        "Survival",
        "Willpower",
    ],
    ids=lambda n: f"stdskill-{n}",
)
def test_standard_skill_updates(client, skill_name):
    """
    For each common standard skill, ensure we can set include/value via REST and it persists.
    Each parameter appears as an individual test case in pytest output.
    """
    from enemygen.models import EnemySkill

    c, _u, _rs, _race, et = _setup_env(client)
    resp, new_id = _clone(c, et.id)

    es = EnemySkill.objects.filter(enemy_template_id=new_id, skill__name=skill_name).first()
    if not es:
        pytest.skip(f"Standard skill '{skill_name}' not present in cloned template")

    # Set include and value deterministically
    r1 = c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_include', 'value': 'true', 'parent_id': None}, content_type='application/json')
    assert r1.status_code == 200
    r2 = c.post(reverse('submit', args=[es.id]), data={'object': 'et_skill_value', 'value': '15', 'parent_id': None}, content_type='application/json')
    assert r2.status_code == 200

    es_ref = EnemySkill.objects.get(id=es.id)
    assert (es_ref.include is True) and (str(es_ref.die_set) == '15')

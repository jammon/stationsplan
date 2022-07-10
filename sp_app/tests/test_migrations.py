import pytest
from django.contrib.sites.models import Site


@pytest.mark.django_db
def test_company_migration():
    """Test the creation of sites in sp_app/migrations/0063_make_sites.py"""
    sites = dict((s.id, (s.domain, s.name)) for s in Site.objects.all())
    assert len(sites) == 3
    for id, domain, name in (
        (1, "localhost:8000", "dev"),
        (2, "stationsplan.de", "Stationsplan.de"),
        (3, "stpst.uber.space", "staging"),
    ):
        assert sites[id] == (domain, name)

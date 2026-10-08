"""El puntaje de Instagram no tenía regla medida: devolvía 0 fijo ('Pendiente').
Sin regla ni datos, debe ser None, no 0."""
from whitebox.instagram_auditor import InstagramAuditor


def test_score_instagram_sin_regla_es_none():
    assert InstagramAuditor()._calculate_score() is None

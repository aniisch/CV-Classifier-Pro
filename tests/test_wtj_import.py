import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Project, WtjCandidate
from src.services import wtj_import

HEADER = "reference;prenom;nom;annees_exp;exp_ok;rep_exp;cv_fichier;lien_wtj\n"


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/t.db")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    session.add(Project(id="p1", name="P"))
    session.commit()
    return session


def write_csv(tmp_path, body, header=HEADER):
    path = tmp_path / "c.csv"
    path.write_text("\ufeff" + header + body, encoding="utf-8")
    return str(path)


def test_import_and_upsert(db, tmp_path):
    path = write_csv(
        tmp_path,
        "r1;Ana;Roy;5,5;False;5 ans;ana.pdf;http://w/1\nr2;Bob;Lee;;True;x;;http://w/2\n",
    )
    assert wtj_import.import_csv(db, "p1", path) == {"created": 1, "updated": 0, "total": 1}
    cand = db.query(WtjCandidate).one()
    assert (cand.years_exp, cand.exp_ok, cand.extra) == (5.5, False, {"rep_exp": "5 ans"})

    path = write_csv(tmp_path, "r1;Ana;Roy;6;True;5 ans;ana.pdf;http://w/1\n")
    assert wtj_import.import_csv(db, "p1", path)["updated"] == 1
    assert db.query(WtjCandidate).one().exp_ok is True


def test_missing_cv_column(db, tmp_path):
    path = write_csv(tmp_path, "r1;Ana\n", header="reference;prenom\n")
    with pytest.raises(ValueError):
        wtj_import.import_csv(db, "p1", path)


@pytest.mark.parametrize(
    "lo,hi,kept,excluded",
    [
        (1, 3, ["a.pdf", "b.pdf", "u.pdf"], ["c.pdf"]),
        (None, 1, ["a.pdf", "u.pdf"], ["b.pdf", "c.pdf"]),
        (3, None, ["c.pdf", "u.pdf"], ["a.pdf", "b.pdf"]),
        (None, None, ["a.pdf", "b.pdf", "c.pdf", "u.pdf"], []),
    ],
)
def test_filter_by_experience(db, lo, hi, kept, excluded):
    for name, years in [("a.pdf", 1.0), ("b.pdf", 2.0), ("c.pdf", 4.0)]:
        db.add(WtjCandidate(project_id="p1", cv_fichier=name, years_exp=years))
    db.commit()
    res = wtj_import.filter_by_experience(db, "p1", ["a.pdf", "b.pdf", "c.pdf", "u.pdf"], lo, hi)
    assert sorted(res["kept"]) == sorted(kept)
    assert res["excluded"] == excluded or sorted(res["excluded"]) == sorted(excluded)
    assert (res["unknown"] == ["u.pdf"]) == (lo is not None or hi is not None)

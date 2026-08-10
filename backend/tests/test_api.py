from fastapi.testclient import TestClient

from app.examples import EXAMPLES
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_examples_endpoint_returns_preloaded_examples():
    response = client.get("/api/examples")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(EXAMPLES)
    ids = {ex["id"] for ex in body}
    assert "wyndor-glass" in ids


def test_solve_endpoint_wyndor_glass():
    example = next(ex for ex in EXAMPLES if ex["id"] == "wyndor-glass")
    response = client.post("/api/solve", json=example["request"])
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "optimal"
    assert body["solution"]["x1"]["decimal"] == 2.0
    assert body["solution"]["x2"]["decimal"] == 6.0
    assert body["z"]["num"] == 36
    assert body["z"]["den"] == 1
    assert body["has_alternate_optima"] is False
    assert body["is_degenerate"] is False
    assert len(body["iterations"]) >= 1
    assert body["standard_form"]["var_names"]
    assert body["graphical"] is not None
    assert body["graphical"]["var_names"] == ["x1", "x2"]
    assert len(body["graphical"]["optimal_vertices"]) == 1
    assert body["graphical"]["optimal_vertices"][0]["x"]["num"] == 2
    assert body["graphical"]["optimal_vertices"][0]["y"]["num"] == 6

    assert body["sensitivity"] is not None
    prices = {
        r["constraint_name"]: r["shadow_price"]["num"] for r in body["sensitivity"]["rhs_ranges"]
    }
    assert prices["Planta 3"] == 1

    assert body["dual"] is not None
    assert body["dual"]["dual_sense"] == "min"
    assert body["dual"]["primal_z"] == body["dual"]["dual_z"]
    assert body["dual"]["strong_duality_holds"] is True
    assert all(item["holds"] for item in body["dual"]["complementary_slackness"])


def test_solve_endpoint_branch_and_bound_example():
    example = next(ex for ex in EXAMPLES if ex["id"] == "programacion-entera")
    response = client.post("/api/solve", json=example["request"])
    assert response.status_code == 200
    body = response.json()

    # The LP relaxation shown in the main tableau is fractional (3, 1.5, Z=21)...
    assert body["status"] == "optimal"
    assert body["z"]["num"] == 21
    assert body["z"]["den"] == 1

    # ...while Branch & Bound finds the true integer optimum (4, 0, Z=20).
    assert body["branch_and_bound"] is not None
    assert body["branch_and_bound"]["status"] == "optimal"
    assert body["branch_and_bound"]["solution"]["x1"]["num"] == 4
    assert body["branch_and_bound"]["solution"]["x2"]["num"] == 0
    assert body["branch_and_bound"]["z"]["num"] == 20
    assert len(body["branch_and_bound"]["nodes"]) >= 1


def test_solve_endpoint_omits_branch_and_bound_when_all_variables_continuous():
    example = next(ex for ex in EXAMPLES if ex["id"] == "wyndor-glass")
    response = client.post("/api/solve", json=example["request"])
    assert response.json()["branch_and_bound"] is None


def test_solve_endpoint_omits_graphical_data_for_more_than_two_variables():
    response = client.post(
        "/api/solve",
        json={
            "sense": "max",
            "objective": [1, 1, 1],
            "constraints": [{"coeffs": [1, 1, 1], "op": "<=", "rhs": 10}],
        },
    )
    assert response.status_code == 200
    assert response.json()["graphical"] is None


def test_solve_endpoint_with_big_m_method():
    example = next(ex for ex in EXAMPLES if ex["id"] == "mezcla-restricciones")
    payload = {**example["request"], "method": "big_m"}
    response = client.post("/api/solve", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "optimal"
    assert body["method"] == "big_m"
    assert body["z"]["num"] == 17
    assert body["z"]["den"] == 5


def test_solve_endpoint_unbounded_and_infeasible():
    unbounded = {
        "sense": "max",
        "objective": [1, 1],
        "constraints": [{"coeffs": [1, -1], "op": "<=", "rhs": 1}],
    }
    response = client.post("/api/solve", json=unbounded)
    assert response.status_code == 200
    assert response.json()["status"] == "unbounded"

    infeasible = {
        "sense": "max",
        "objective": [1, 1],
        "constraints": [
            {"coeffs": [1, 1], "op": "<=", "rhs": 2},
            {"coeffs": [1, 1], "op": ">=", "rhs": 6},
        ],
    }
    response = client.post("/api/solve", json=infeasible)
    assert response.status_code == 200
    assert response.json()["status"] == "infeasible"


def test_solve_endpoint_rejects_mismatched_dimensions():
    bad_request = {
        "sense": "max",
        "objective": [1, 1, 1],
        "constraints": [{"coeffs": [1, 1], "op": "<=", "rhs": 2}],
    }
    response = client.post("/api/solve", json=bad_request)
    assert response.status_code == 422
    assert "coeficientes" in response.json()["detail"]


def test_solve_endpoint_rejects_empty_constraints():
    bad_request = {"sense": "max", "objective": [1, 1], "constraints": []}
    response = client.post("/api/solve", json=bad_request)
    assert response.status_code == 422


def test_solve_endpoint_rejects_invalid_numeric_literal():
    bad_request = {
        "sense": "max",
        "objective": [1, 1],
        "constraints": [{"coeffs": [1, "not-a-number"], "op": "<=", "rhs": 2}],
    }
    response = client.post("/api/solve", json=bad_request)
    assert response.status_code == 422

def test_list_homes_returns_all_homes(client, db):
    """
    Test that GET /api/v1/home/ returns a list of all homes in the DB.
    """
    # 1. ARRANGE: Manually add two homes to our test database
    home_1 = models.Home(name="Main House", council="Milton Keynes", active=True)
    home_2 = models.Home(name="Summer Cottage", council="Bucks", active=False)

    db.add(home_1)
    db.add(home_2)
    db.commit()

    # 2. ACT: Call the FastAPI endpoint
    response = client.get("/api/v1/home/")

    # 3. ASSERT: Check status code and data integrity
    assert response.status_code == 200

    data = response.json()
    assert "homes" in data
    assert len(data["homes"]) == 2

    # Verify specific data points
    names = [h["name"] for h in data["homes"]]
    assert "Main House" in names
    assert "Summer Cottage" in names

    # Verify the JSON format (Snake Case vs Camel Case)
    assert data["homes"][0]["council"] == "Milton Keynes"


def test_list_homes_empty_db(client):
    """
    Test that the endpoint returns an empty list if no homes exist.
    """
    response = client.get("/api/v1/home/")

    assert response.status_code == 200
    assert response.json() == {"homes": []}
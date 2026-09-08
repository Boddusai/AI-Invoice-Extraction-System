import requests


BASE_URL = "http://127.0.0.1:8000"


def check(
    name,
    url,
):
    try:

        response = requests.get(
            url,
            timeout=10,
        )

        if response.status_code == 200:

            print(
                f"[PASS] {name}"
            )

            return True

        print(
            f"[FAIL] {name} "
            f"- HTTP "
            f"{response.status_code}"
        )

        return False

    except Exception as error:

        print(
            f"[FAIL] {name} "
            f"- {error}"
        )

        return False


def main():

    print()
    print(
        "AI Invoice System "
        "Smoke Test"
    )

    print("=" * 50)

    tests = [
        (
            "Root API",
            f"{BASE_URL}/",
        ),

        (
            "Health",
            f"{BASE_URL}/health",
        ),

        (
            "Database",
            f"{BASE_URL}/database-health",
        ),

        (
            "API Info",
            f"{BASE_URL}/api-info",
        ),

        (
            "Invoice List",
            f"{BASE_URL}/api/invoices",
        ),
    ]

    results = []

    for name, url in tests:

        results.append(
            check(
                name,
                url,
            )
        )

    print("=" * 50)

    passed = sum(
        results
    )

    total = len(
        results
    )

    print(
        f"Passed: "
        f"{passed}/{total}"
    )

    if passed == total:

        print(
            "Backend smoke test "
            "completed successfully!"
        )

    else:

        print(
            "Some backend tests failed."
        )


if __name__ == "__main__":
    main()
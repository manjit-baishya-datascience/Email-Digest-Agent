from graph import build_graph

if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({})

    if result.get("error"):
        print(f"Failed: {result['error']}")
    else:
        print(f"Success! Digest saved to: {result['output_path']}")
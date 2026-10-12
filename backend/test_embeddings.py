
from fastembed import TextEmbedding


def main() -> None:
    model = TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )

    texts = [
        "Avoid arbitrary z-index values unless documented.",
        "The header should follow the application's layering conventions.",
        "Database connections must use secure credentials.",
    ]

    vectors = list(model.embed(texts))

    print("Texts embedded:", len(vectors))
    print("Vector dimensions:", len(vectors[0]))
    print("First vector sample:", vectors[0][:5].tolist())

    assert len(vectors) == len(texts)
    assert all(len(vector) == 384 for vector in vectors)

    print("Embedding test successful.")


if __name__ == "__main__":
    main()

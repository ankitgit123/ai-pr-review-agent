
function App() {
  return (
    <main
      style={{
        maxWidth: "900px",
        margin: "80px auto",
        padding: "24px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1>AI PR Review Agent</h1>

      <p>
        Review pull requests for potential bugs, security issues, and coding
        standard violations.
      </p>

      <section>
        <h2>Application status</h2>
        <p>Frontend initialized successfully.</p>
        <p>Backend API: http://localhost:8000</p>
      </section>
    </main>
  );
}

export default App;

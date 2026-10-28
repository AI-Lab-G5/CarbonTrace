export function Footer() {
  const anoAtual = new Date().getFullYear();

  return (
    <footer className="wrap">
      <p>Demonstração — CarbonTrace · {anoAtual}</p>
    </footer>
  );
}


const request = require("supertest");
const { app } = require("../api/src/app");

describe("Isolamento de tenant", () => {
  it("usuário da empresa A recebe 403 ou 404 ao acessar dados da empresa B", async () => {
    const tokenA = await login("usuario@empresaA.com"); // helper a implementar depois
    const res = await request(app)
      .get("/api/empresas/empresa-b/documentos")
      .set("Authorization", `Bearer ${tokenA}`);

    expect([403, 404]).toContain(res.status);
  });
});

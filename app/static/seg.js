async function sg(){
  const d = await api("seguranca");
  const t = document.getElementById("sgt"), r = document.getElementById("sgr");
  t.textContent = ""; r.textContent = "";
  if (d.erro) { t.textContent = "Erro: " + d.erro; return; }
  Object.entries(d.totais).forEach(([k, v]) => {
    const s = document.createElement("div");
    s.textContent = k + ": " + v;
    s.className = k === "PASS" ? "ok" : "er";
    t.append(s);
  });
  d.recentes.forEach(i => {
    const c = document.createElement("div");
    c.className = "c";
    c.textContent = i.estado + " | " + i.evento + " | " + (i.motivo || "-") + " | " + new Date(i.quando).toLocaleString("pt-BR");
    r.append(c);
  });
}
document.querySelector("button[data-s=seg]").addEventListener("click", sg);

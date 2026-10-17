(function () {
  var sec = document.getElementById("treino");
  sec.textContent = "";
  var h = document.createElement("h2");
  h.textContent = "Treino do Turing protetor";
  var p = document.createElement("p");
  p.style.color = "#8a94a3";
  p.textContent = "Revise os eventos reais. Sua decisao ensina o Turing o que e ataque, falso positivo ou conhecido.";
  var box = document.createElement("div");
  sec.append(h, p, box);
  var ROT = { ataque: "Ataque", falso_positivo: "Falso positivo", conhecido: "Conhecido" };

  async function decidir(id, d) {
    await api("revisao", { method: "POST", body: JSON.stringify({ id: id, decisao: d }) });
    carregar();
  }

  async function carregar() {
    var d = await api("revisao");
    box.textContent = "";
    if (d.erro) { box.textContent = "Erro: " + d.erro; return; }
    d.itens.forEach(function (i) {
      var c = document.createElement("div");
      c.className = "c";
      var t = document.createElement("div");
      t.textContent = i.estado + " | " + i.evento + " | " + (i.motivo || "-") + " | " + new Date(i.quando).toLocaleString("pt-BR");
      c.append(t);
      if (i.decisao) {
        var s = document.createElement("div");
        s.className = "ok";
        s.textContent = "Revisado: " + ROT[i.decisao];
        c.append(s);
      }
      Object.keys(ROT).forEach(function (k) {
        var b = document.createElement("button");
        b.className = "p";
        b.style.cssText = "margin:8px 8px 0 0;opacity:" + (i.decisao === k ? "1" : "0.6");
        b.textContent = ROT[k];
        b.onclick = function () { decidir(i.id, k); };
        c.append(b);
      });
      box.append(c);
    });
  }
  document.querySelector("button[data-s=treino]").addEventListener("click", carregar);
})();

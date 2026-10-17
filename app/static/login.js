(function () {
  var guardado = sessionStorage.getItem("tk") || "";
  if (guardado) return;
  var box = document.createElement("div");
  box.style.cssText = "position:fixed;inset:0;background:#0e1116;display:flex;align-items:center;justify-content:center;z-index:99";
  var f = document.createElement("form");
  f.style.cssText = "background:#171b22;border:1px solid #262c36;border-radius:12px;padding:24px;width:320px;max-width:90vw";
  f.innerHTML = "<h3 style=\"margin:0 0 12px;color:#2dd4bf\">Turing Admin</h3>" +
    "<input type=\"text\" name=\"username\" value=\"admin\" autocomplete=\"username\" style=\"display:none\">" +
    "<input id=\"lg-tk\" type=\"password\" name=\"password\" autocomplete=\"current-password\" placeholder=\"Token de administrador\" style=\"width:100%;box-sizing:border-box;padding:10px;margin-bottom:10px;background:#0e1116;border:1px solid #262c36;color:#e6e9ee;border-radius:8px\">" +
    "<button class=\"p\" type=\"submit\" style=\"width:100%\">Entrar</button><p id=\"lg-er\" style=\"color:#f87171;margin:8px 0 0\"></p>";
  f.onsubmit = async function (e) {
    e.preventDefault();
    var t = document.getElementById("lg-tk").value;
    var r = await fetch("/admin/api/status", { headers: { "X-Admin-Token": t } });
    if (r.status === 401) { document.getElementById("lg-er").textContent = "Token inválido"; return; }
    sessionStorage.setItem("tk", t);
    location.reload();
  };
  box.append(f);
  document.body.append(box);
})();

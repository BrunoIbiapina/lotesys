// static/admin/venda_toggle.js
(function() {
  function toggleLote() {
    var unidade = document.getElementById("id_unidade_vendida");
    var loteRow = document.querySelector(".form-row.field-lote, .field-lote"); // jazzmin/admin diferentes
    if (!unidade || !loteRow) return;

    if (unidade.value === "LOTE") {
      loteRow.style.display = "";
    } else {
      loteRow.style.display = "none";
      // limpa o valor do select para evitar validação se trocar para HECTARE
      var loteSelect = document.getElementById("id_lote");
      if (loteSelect) {
        if ("value" in loteSelect) loteSelect.value = "";
      }
    }
  }

  document.addEventListener("DOMContentLoaded", function() {
    var unidade = document.getElementById("id_unidade_vendida");
    if (!unidade) return;
    toggleLote();
    unidade.addEventListener("change", toggleLote);
  });
})();
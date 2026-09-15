/* ============================================================
   Autosul — UTM Bridge
   A ponte entre o link com UTM e o envio do formulário da LP.

   O que faz, nesta ordem:
   1. Lê as UTMs da URL quando o visitante chega na LP.
   2. Guarda por 30 dias — sobrevive a recarregar a página, fechar
      o navegador e navegar entre as páginas da LP.
   3. Preenche campos ocultos em TODO <form> da página, para os
      valores chegarem junto com o lead (e-mail, CRM, planilha).

   Instalação: <script src="/js/utm-bridge.js" defer></script>
   ============================================================ */
(function (window, document) {
  'use strict';

  // ---------- Configuração ----------

  // 'ultimo'  = vale o link mais recente que a pessoa clicou (padrão:
  //             é o critério justo quando cada vendedor tem seu link).
  // 'primeiro'= vale o primeiro link que trouxe a pessoa.
  var ATRIBUICAO = 'ultimo';

  var VALIDADE_MS = 30 * 24 * 60 * 60 * 1000; // 30 dias
  var CHAVE = 'autosul.utm';
  var MAX = 120; // corta valores absurdos antes de mandar pro form

  var CAMPOS = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
    'gclid', 'fbclid'
  ];

  // ---------- Leitura ----------

  function normalizar(campo, valor) {
    var v = String(valor).trim().slice(0, MAX);
    // utm_* é case-sensitive no GA4: "Nedja" e "nedja" viram duas linhas.
    // gclid/fbclid são IDs — não podem ser alterados.
    return campo.indexOf('utm_') === 0 ? v.toLowerCase() : v;
  }

  function daURL() {
    var busca = new URLSearchParams(window.location.search);
    var out = {};
    CAMPOS.forEach(function (campo) {
      var v = busca.get(campo);
      if (v) out[campo] = normalizar(campo, v);
    });
    return out;
  }

  function lerGuardado() {
    try {
      var bruto = window.localStorage.getItem(CHAVE);
      if (!bruto) return null;
      var dado = JSON.parse(bruto);
      if (!dado || !dado.em || Date.now() - dado.em > VALIDADE_MS) return null;
      return dado.valores || null;
    } catch (e) {
      return null; // modo anônimo ou storage bloqueado
    }
  }

  function guardar(valores) {
    try {
      window.localStorage.setItem(CHAVE, JSON.stringify({
        em: Date.now(),
        valores: valores
      }));
    } catch (e) {
      // Sem persistência: a UTM ainda funciona nesta página.
    }
  }

  // ---------- Estado ----------

  var novas = daURL();
  var guardadas = lerGuardado();
  var temNovas = Object.keys(novas).length > 0;
  var valores;

  if (temNovas && (ATRIBUICAO === 'ultimo' || !guardadas)) {
    valores = novas;
    valores.pagina_entrada = window.location.href.split('#')[0].slice(0, 300);
    valores.referrer = (document.referrer || '').slice(0, 300);
    valores.data_clique = new Date().toISOString();
    guardar(valores);
  } else {
    valores = guardadas || {};
  }

  // ---------- Formulários ----------

  function aplicar(form) {
    if (!form || form.nodeName !== 'FORM') return;
    Object.keys(valores).forEach(function (nome) {
      var valor = valores[nome];
      if (!valor) return;
      var campo = form.querySelector('[name="' + nome + '"]');
      if (!campo) {
        campo = document.createElement('input');
        campo.type = 'hidden';
        campo.name = nome;
        form.appendChild(campo);
      }
      // Nunca sobrescreve algo que a pessoa digitou.
      if (campo.type === 'hidden' || !campo.value) campo.value = valor;
    });
  }

  function aplicarEmTodos() {
    var forms = document.querySelectorAll('form');
    for (var i = 0; i < forms.length; i++) aplicar(forms[i]);
  }

  // Rede de segurança: pega formulários criados depois do load
  // (popup, modal, React). Fase de captura = roda antes do handler
  // do form montar o FormData.
  document.addEventListener('submit', function (ev) {
    aplicar(ev.target);
  }, true);

  // ---------- Links internos ----------

  function query() {
    var partes = [];
    CAMPOS.forEach(function (campo) {
      if (valores[campo]) {
        partes.push(campo + '=' + encodeURIComponent(valores[campo]));
      }
    });
    return partes.join('&');
  }

  // Carrega as UTMs para as outras páginas da LP. Só mesma origem —
  // nunca vaza parâmetro para domínio de terceiro.
  function propagar() {
    if (!query()) return;
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      var url;
      try {
        url = new URL(link.href, window.location.href);
      } catch (e) {
        continue;
      }
      if (url.origin !== window.location.origin) continue;
      if (url.searchParams.has('utm_source')) continue;
      CAMPOS.forEach(function (campo) {
        if (valores[campo]) url.searchParams.set(campo, valores[campo]);
      });
      link.href = url.toString();
    }
  }

  // Opt-in: <a href="https://wa.me/55..." data-utm-whatsapp>
  // Marca a mensagem com o vendedor, para quem atende no WhatsApp
  // saber de qual link veio sem depender do formulário.
  function marcarWhatsapp() {
    var marca = valores.utm_content || valores.utm_source;
    if (!marca) return;
    var links = document.querySelectorAll('a[data-utm-whatsapp][href]');
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      var url;
      try {
        url = new URL(link.href, window.location.href);
      } catch (e) {
        continue;
      }
      if (!/(^|\.)wa\.me$|(^|\.)whatsapp\.com$/.test(url.hostname)) continue;
      var texto = url.searchParams.get('text') || '';
      if (texto.indexOf('[origem:') !== -1) continue; // já marcado
      url.searchParams.set('text', (texto + ' [origem: ' + marca + ']').trim());
      link.href = url.toString();
    }
  }

  // ---------- GA4 / GTM ----------

  if (window.dataLayer && typeof window.dataLayer.push === 'function') {
    var evento = { event: 'utm_ponte' };
    Object.keys(valores).forEach(function (k) { evento[k] = valores[k]; });
    window.dataLayer.push(evento);
  }

  // ---------- API pública ----------
  // Para form que envia JSON via fetch/React, use AutosulUTM.get()
  // e mande o objeto junto no payload.
  window.AutosulUTM = {
    get: function () {
      var copia = {};
      Object.keys(valores).forEach(function (k) { copia[k] = valores[k]; });
      return copia;
    },
    query: query,
    aplicar: aplicar,
    aplicarEmTodos: aplicarEmTodos,
    esquecer: function () {
      try { window.localStorage.removeItem(CHAVE); } catch (e) {}
    }
  };

  // ---------- Start ----------

  function iniciar() {
    aplicarEmTodos();
    propagar();
    marcarWhatsapp();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }

})(window, document);

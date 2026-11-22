/* Property Rent Hub: navigation, office enquiry form (to WhatsApp) and click tracking.
   No dependencies. Works without analytics; when GA4 (gtag) or Google Tag Manager
   (dataLayer) is installed, WhatsApp, phone and form events are sent.
   Personal details typed into the form are never sent to analytics. */
(function () {
  "use strict";

  var doc = document;
  var header = doc.querySelector(".site-header");

  /* ---------------------------------------------------------------- menu */
  var toggle = doc.querySelector(".menu-toggle");
  if (toggle && header) {
    toggle.addEventListener("click", function () {
      var open = header.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  function closeMenus(except) {
    doc.querySelectorAll(".primary-nav details[open]").forEach(function (d) {
      if (d !== except) d.removeAttribute("open");
    });
  }
  doc.addEventListener("click", function (e) {
    var inside = e.target.closest && e.target.closest(".primary-nav details");
    closeMenus(inside);
  });
  doc.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closeMenus(null);
      if (header && header.classList.contains("nav-open") && toggle) {
        header.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    }
  });

  /* ------------------------------------------------------------ tracking */
  function track(name, params) {
    try {
      var clean = {};
      for (var k in params) { if (params[k]) clean[k] = params[k]; }
      window.dataLayer = window.dataLayer || [];
      var payload = { event: name };
      for (var j in clean) payload[j] = clean[j];
      window.dataLayer.push(payload);
      if (typeof window.gtag === "function") window.gtag("event", name, clean);
    } catch (err) { /* tracking must never block the visitor */ }
  }
  var pageType = doc.body.getAttribute("data-page-type") || "";

  doc.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a");
    if (!a) return;
    if (a.hasAttribute("data-wa")) {
      track("whatsapp_click", {
        link_placement: a.getAttribute("data-wa"),
        office_area: a.getAttribute("data-area"),
        property_ref: a.getAttribute("data-ref"),
        page_type: pageType
      });
    } else if ((a.getAttribute("href") || "").indexOf("tel:") === 0) {
      track("phone_click", { link_placement: a.getAttribute("data-place"), page_type: pageType });
    }
  });

  /* ------------------------------------------------- enquiry form → WhatsApp */
  function fieldValue(form, el) {
    if (el.tagName === "SELECT") {
      var opt = el.options[el.selectedIndex];
      return el.value ? (opt.getAttribute("data-text") || opt.text) : "";
    }
    return (el.value || "").trim();
  }

  doc.querySelectorAll("form[data-enquiry]").forEach(function (form) {
    var number = form.getAttribute("data-number");
    var source = form.getAttribute("data-source") || "Website";
    var status = form.querySelector("[data-status]");
    var phone = form.elements.phone;

    // A phone number needs at least 7 digits; spaces, +, brackets and dashes are fine.
    function checkPhone() {
      if (!phone) return;
      var digits = (phone.value.match(/[0-9]/g) || []).length;
      phone.setCustomValidity(phone.value && digits < 7 ? "Enter a phone number with the country code, for example +971 50 123 4567" : "");
    }
    if (phone) phone.addEventListener("input", checkPhone);

    function message() {
      var lines = ["*Office enquiry from the Property Rent Hub website*"];
      var office = form.getAttribute("data-office");
      if (office) lines.push("*Office:* " + office);
      form.querySelectorAll("[data-label]").forEach(function (el) {
        var v = fieldValue(form, el);
        if (v) lines.push("*" + el.getAttribute("data-label") + ":* " + v.replace(/\s+/g, " "));
      });
      lines.push("Sent from: " + source);
      lines.push("Ref: " + (form.getAttribute("data-ref") || "WEB-FORM"));
      return lines.join("\n");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      checkPhone();
      if (form.checkValidity && !form.checkValidity()) {
        if (form.reportValidity) form.reportValidity();
        return;
      }
      var url = "https://wa.me/" + number + "?text=" + encodeURIComponent(message());
      var area = form.elements.location ? form.elements.location.value : "";
      track("generate_lead", {
        form_name: "office_enquiry",
        link_placement: form.getAttribute("data-placement"),
        office_area: area,
        team_size: form.elements.people ? form.elements.people.value : "",
        office_type: form.elements.type ? form.elements.type.value : "",
        property_ref: form.getAttribute("data-ref-code"),
        page_type: pageType
      });
      track("whatsapp_click", { link_placement: "enquiry-form", office_area: area, page_type: pageType });
      if (status) {
        status.innerHTML = "";
        var p = doc.createElement("p");
        p.style.margin = "0";
        p.appendChild(doc.createTextNode("WhatsApp is opening with your enquiry. Tap Send in WhatsApp so it reaches us. If it did not open, "));
        var a = doc.createElement("a");
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = "open WhatsApp here";
        p.appendChild(a);
        p.appendChild(doc.createTextNode("."));
        status.appendChild(p);
      }
      // window.open returns null when a pop-up is blocked; then use this tab instead.
      var w = null;
      try { w = window.open(url, "_blank"); } catch (err) { w = null; }
      if (w) {
        try { w.opener = null; } catch (err3) { /* ignore */ }
      } else {
        try { window.location.href = url; } catch (err2) { /* the link in the status message still works */ }
      }
    });
  });
})();

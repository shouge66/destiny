import { ROUTES } from "./config.js";
import { initDataCosmos } from "./cosmos.js";
import { state } from "./state.js";
import {
  renderAssessment,
  renderDashboard,
  renderLogin,
  renderPlan,
  renderPrivacy,
  renderProfile,
} from "./views.js";

const app = document.getElementById("app");
const nav = document.getElementById("main-nav");
let cleanupCosmos = null;

function drawNav() {
  nav.innerHTML = ROUTES.map((route) => {
    if (!state.auth) {
      return "";
    }
    const active = location.hash === route.path ? "active" : "";
    return `<a class="${active}" href="${route.path}">${route.label}</a>`;
  }).join("");
}

async function renderRoute() {
  const hash = location.hash || "#/login";
  if (!state.auth && hash !== "#/login") {
    location.hash = "#/login";
    return;
  }

  drawNav();
  app.innerHTML = document.getElementById("loading-template").innerHTML;

  try {
    switch (hash) {
      case "#/login":
        renderLogin(app);
        break;
      case "#/dashboard":
        await renderDashboard(app);
        break;
      case "#/assessment":
        renderAssessment(app);
        break;
      case "#/profile":
        await renderProfile(app);
        break;
      case "#/plan":
        await renderPlan(app);
        break;
      case "#/privacy":
        renderPrivacy(app);
        break;
      default:
        location.hash = state.auth ? "#/dashboard" : "#/login";
    }
  } catch (error) {
    app.innerHTML = `<section class="panel"><h2>页面加载失败</h2><p>${error.message}</p></section>`;
  }

  app.classList.remove("route-enter");
  // Force reflow so the entry animation restarts on each route render.
  void app.offsetWidth;
  app.classList.add("route-enter");
}

window.addEventListener("hashchange", renderRoute);
window.addEventListener("DOMContentLoaded", () => {
  const cosmosCanvas = document.getElementById("data-cosmos");
  cleanupCosmos = initDataCosmos(cosmosCanvas);

  if (!location.hash) {
    location.hash = state.auth ? "#/dashboard" : "#/login";
  }
  renderRoute();
});

window.addEventListener("beforeunload", () => {
  if (cleanupCosmos) {
    cleanupCosmos();
    cleanupCosmos = null;
  }
});

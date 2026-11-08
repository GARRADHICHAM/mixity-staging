// Pages du site marketing (Webflow), atteintes depuis les boutons des pages d'atterrissage.
// Le domaine vient du serveur (réglage MARKETING_SITE_URL, variable d'environnement du même nom).
const MARKETING_PAGES = {
	diag: '/solutions/diag',
	human: '/solutions/human',
	measure360: '/solutions/360',
	demo: '/demo',
	pricing: '/tarifs',
	partners: '/partenaires',
	example: '/empreintes', // exemples de résultats publiés
};

const marketingBaseUrl = () => (window.marketing_site_url || 'https://www.mixity.io').replace(/\/$/, '');

export const openMarketingPage = (page) => {
	window.location.href = marketingBaseUrl() + MARKETING_PAGES[page];
};

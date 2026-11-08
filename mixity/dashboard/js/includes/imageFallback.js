// Visuel absent de Cloudinary (lien KO) : affichage d'une image par défaut.
const useDefaultImage = (src) => (e) => {
	if (e.currentTarget.src.endsWith(src)) return;
	e.currentTarget.src = src;
};

export const useDefaultSolutionImage = useDefaultImage('/static/solvers_catalog/solution.jpg');
export const useDefaultBestPracticeImage = useDefaultImage('/static/best_practices_catalog/best_practice.jpg');
export const useDefaultLogo = useDefaultImage('/static/icon/buildings.svg');

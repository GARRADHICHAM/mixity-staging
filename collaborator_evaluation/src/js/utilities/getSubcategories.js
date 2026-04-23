function getSubcategories(questionnaire) {
	const subcategories = {};
	questionnaire.forEach((question) => {
		if (question.category !== undefined) {
			if (!(question.category.name in subcategories)) {
				subcategories[question.category.name] = [];
			}
			question.subcategory.color = question.category.color;
			subcategories[question.category.name].push(question.subcategory);
		} else {
			subcategories[question.subcategory.name] = [];
		}
	});
	for (let key in subcategories) {
		if (subcategories[key].length > 0) {
			subcategories[key] = subcategories[key].reduce((unique, o) => {
				if (!unique.some((obj) => obj.slug === o.slug && obj.name === o.name)) {
					unique.push(o);
				}
				return unique;
			}, []);
		}
	}
	return subcategories;
}

export default getSubcategories;

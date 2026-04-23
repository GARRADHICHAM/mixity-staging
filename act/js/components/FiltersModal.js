import React, { useEffect, useState } from 'react';
import { Modal, Button, Form } from 'react-bootstrap';

function FiltersModal({ display, handleClose, filters, setFilters, elearnings }) {
	const [notionsList, setNotionsList] = useState(new Set());
	const [categoriesList, setCategoriesList] = useState(new Set());
	const [languagesList, setLanguagesList] = useState(new Set());
	const [keywordsList, setKeywordsList] = useState(new Set());
	const [evaluationMethodsList, setEvaluationMethodsList] = useState(new Set());

	useEffect(() => {
		const newNotionsSet = new Set();
		const newCategoriesSet = new Set();
		const newLanguagesSet = new Set();
		const newKeywordsSet = new Set();
		const newEvaluationMethodsSet = new Set();

		for (let elearning of elearnings) {
			for (let notion of elearning.notions) {
				if (![...newNotionsSet].some((item) => item.slug === notion.slug)) {
					newNotionsSet.add(notion);
				}
			}
			for (let category of elearning.category) {
				if (![...newCategoriesSet].some((item) => item.slug === category.slug)) {
					newCategoriesSet.add(category);
				}
			}
			for (let language of elearning.languages) {
				if (![...newLanguagesSet].some((item) => item.code === language.code)) {
					newLanguagesSet.add(language);
				}
			}
			for (let keyword of elearning.keywords) {
				if (![...newKeywordsSet].some((item) => item.slug === keyword.slug)) {
					newKeywordsSet.add(keyword);
				}
			}
			for (let evaluationMethod of elearning.evaluation_methods) {
				if (![...newEvaluationMethodsSet].some((item) => item.slug === evaluationMethod.slug)) {
					newEvaluationMethodsSet.add(evaluationMethod);
				}
			}
		}

		setNotionsList(newNotionsSet);
		setCategoriesList(newCategoriesSet);
		setLanguagesList(newLanguagesSet);
		setKeywordsList(newKeywordsSet);
		setEvaluationMethodsList(newEvaluationMethodsSet);
	}, [elearnings]);

	const updateFilter = (type, slug, checked) => {
		setFilters((prevFilters) => {
			const updatedFilters = { ...prevFilters };

			if (checked) {
				if (!updatedFilters[type].includes(slug)) {
					updatedFilters[type].push(slug);
				}
			} else {
				updatedFilters[type] = updatedFilters[type].filter((item) => item !== slug);
			}

			return updatedFilters;
		});
	};

	return (
		<Modal
			size="lg"
			show={display}
			onHide={handleClose}
			centered
			aria-labelledby="contained-modal-title-vcenter"
			style={{ zIndex: '1050', width: '100%' }}
			className="m-0 p-0"
		>
			<Modal.Header closeButton>
				<Modal.Title>{gettext('Filtres')}</Modal.Title>
			</Modal.Header>
			<Modal.Body>
				{/* Category */}
				<h6 id="contained-modal-title-vcenter" className="mb-4">
					{gettext('Catégories')}
				</h6>
				<Form className="checkbox__grid">
					{Array.from(categoriesList).map((cat) => (
						<div key={cat.slug} className="checkbox-item">
							<Form.Check
								type="checkbox"
								checked={filters.categoriesFilter.includes(cat.slug)}
								onChange={(e) => updateFilter('categoriesFilter', cat.slug, e.target.checked)}
								value={cat.pk}
								label={cat.name}
							/>
						</div>
					))}
				</Form>
				<hr className="solid" style={{ borderColor: '#DEDFEA' }} />

				{/* Notions */}
				<h6 id="contained-modal-title-vcenter" className="mb-4">
					{gettext('Notions')}
				</h6>
				<Form className="checkbox__grid">
					{Array.from(notionsList).map((notion) => (
						<div key={notion.slug} className="checkbox-item">
							<Form.Check
								type="checkbox"
								checked={filters.notionsFilter.includes(notion.slug)}
								onChange={(e) => updateFilter('notionsFilter', notion.slug, e.target.checked)}
								value={notion.pk}
								label={notion.label}
							/>
						</div>
					))}
				</Form>
				<hr className="solid" style={{ borderColor: '#DEDFEA' }} />

				{/* Languages */}
				<h6 id="contained-modal-title-vcenter" className="mb-4">
					{gettext('Langues')}
				</h6>
				<Form className="checkbox__grid">
					{Array.from(languagesList).map((language) => (
						<div key={language.code} className="checkbox-item">
							<Form.Check
								type="checkbox"
								checked={filters.languagesFilter.includes(language.code)}
								onChange={(e) => updateFilter('languagesFilter', language.code, e.target.checked)}
								value={language.pk}
								label={language.label}
							/>
						</div>
					))}
				</Form>
				<hr className="solid" style={{ borderColor: '#DEDFEA' }} />

				{/* Keywords */}
				<h6 id="contained-modal-title-vcenter" className="mb-4">
					{gettext('Mots-clefs')}
				</h6>
				<Form className="checkbox__grid">
					{Array.from(keywordsList).map((keyword) => (
						<div key={keyword.slug} className="checkbox-item">
							<Form.Check
								type="checkbox"
								checked={filters.keywordsFilter.includes(keyword.slug)}
								onChange={(e) => updateFilter('keywordsFilter', keyword.slug, e.target.checked)}
								value={keyword.pk}
								label={keyword.label}
							/>
						</div>
					))}
				</Form>
				<hr className="solid" style={{ borderColor: '#DEDFEA' }} />

				{/* Evaluation Methods */}
				<h6 id="contained-modal-title-vcenter" className="mb-4">
					{gettext("Méthodes d'évaluation")}
				</h6>
				<Form className="checkbox__grid">
					{Array.from(evaluationMethodsList).map((evaluationMethod) => (
						<div key={evaluationMethod.slug} className="checkbox-item">
							<Form.Check
								type="checkbox"
								checked={filters.evaluationMethodsFilter.includes(evaluationMethod.slug)}
								onChange={(e) => updateFilter('evaluationMethodsFilter', evaluationMethod.slug, e.target.checked)}
								value={evaluationMethod.pk}
								label={evaluationMethod.label}
							/>
						</div>
					))}
				</Form>
			</Modal.Body>
			<Modal.Footer>
				<Button variant="secondary" onClick={handleClose}>
					{gettext('Fermer')}
				</Button>
			</Modal.Footer>
		</Modal>
	);
}

export default FiltersModal;

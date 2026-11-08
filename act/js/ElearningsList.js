import React, { useState, useEffect } from 'react';
import { Breadcrumb, Card, Form } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';
import ElearningsCards from './components/ElearningsCards';
import ElearningsFilters from './components/ElearningsFilters';

function ElearningsList() {
	const [placeholder, setPlaceholder] = useState('Chargement');
	const [elearningsList, setElearningsList] = useState([]);
	const [currentElearningsList, setCurrentElearningsList] = useState([]);
	const [isLoading, setIsLoading] = useState(true);

	const [environmentUrl, setEnvironmentUrl] = useState('');

	const [filters, setFilters] = useState({
		titleFilter: '',
		notionsFilter: [],
		keywordsFilter: [],
		categoriesFilter: [],
		evaluationMethodsFilter: [],
		languagesFilter: [],
	});

	const fetchEnvironmentUrl = () => {
		fetch('/api/url/')
			.then((response) => response.json())
			.then((data) => {
				const domain = data;
				setEnvironmentUrl(`${window.location.protocol}//${domain}/`);
			})
			.then(() => {
				fetchElearningsList();
			})
			.catch(() => {
				setPlaceholder(gettext("Impossible de charger l'URL de l'environnement."));
			});
	};

	const fetchElearningsList = () => {
		fetch(`${environmentUrl}/api/elearning/`)
			.then((response) => response.json())
			.then((data) => {
				setElearningsList(data);
				setCurrentElearningsList(data);
				setIsLoading(false);
				if (data.length === 0) {
					setPlaceholder('Aucun e-learning disponible...');
				}
			})
			.catch(() => {
				setPlaceholder(gettext('Impossible de charger les e-learnings.'));
				setIsLoading(false);
			});
	};

	useEffect(() => {
		fetchEnvironmentUrl();
	}, []);

	useEffect(() => {
		const filteredElearnings = elearningsList.filter((elearning) => {
			const titleMatches = elearning.title.toLowerCase().includes(filters.titleFilter.toLowerCase());

			const categoryMatches =
				filters.categoriesFilter.length === 0 ||
				filters.categoriesFilter.every((selectedCategory) => elearning.category.some((cat) => cat.slug === selectedCategory));

			const notionsMatches =
				filters.notionsFilter.length === 0 ||
				filters.notionsFilter.every((selectedNotion) => elearning.notions.some((notion) => notion.slug === selectedNotion));

			const languagesMatches =
				filters.languagesFilter.length === 0 ||
				filters.languagesFilter.every((selectedLanguage) => elearning.languages.some((language) => language.code === selectedLanguage));

			const keywordsMatches =
				filters.keywordsFilter.length === 0 ||
				filters.keywordsFilter.every((selectedKeyword) => elearning.keywords.some((keyword) => keyword.slug === selectedKeyword));

			const evaluationMethodsMatches =
				filters.evaluationMethodsFilter.length === 0 ||
				filters.evaluationMethodsFilter.every((selectedEvaluationMethods) =>
					elearning.evaluation_methods.some((evaluationMethod) => evaluationMethod.slug === selectedEvaluationMethods),
				);

			return titleMatches && categoryMatches && notionsMatches && languagesMatches && keywordsMatches && evaluationMethodsMatches;
		});

		setCurrentElearningsList(filteredElearnings);
		if (filteredElearnings.length === 0) {
			setPlaceholder('Aucun e-learning correspondant à votre recherche.');
		}
	}, [filters, elearningsList]);

	if (isLoading) {
		return (
			<div className="placeholder">
				<p>{gettext('Chargement...')}</p>
			</div>
		);
	}

	return (
		<div style={{ fontFamily: 'DM Sans' }}>
			<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
				<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
					<Breadcrumb.Item href={'/'} underline="hover" color="inherit">
						{gettext('Accueil')}
					</Breadcrumb.Item>
					<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
					<Breadcrumb.Item underline="hover" color="inherit" active>
						{gettext('Trouver un e-learning')}
					</Breadcrumb.Item>
				</Breadcrumb>
				<Header
					data={{
						url: '/',
						languages: languages,
						language_code: language_code,
						enabled_website_languages: enabled_website_languages,
					}}
				/>
			</div>
			<div className="elearnings-list-component mx-4">
				<ElearningsFilters elearnings={elearningsList} filters={filters} setFilters={setFilters} />
				<ElearningsCards elearnings={currentElearningsList} placeholder={placeholder} environmentUrl={environmentUrl} />
			</div>
		</div>
	);
}

export default ElearningsList;

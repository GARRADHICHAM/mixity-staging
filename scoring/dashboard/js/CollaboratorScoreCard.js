import React, { useState, useEffect } from 'react';
import DisplayScanFootPrint from './includes/components/DisplayScanFootPrint';
import DisplayProfile from './includes/components/DisplayProfile';
import DisplaySkills from './includes/components/DisplaySkills';
import DisplayScoringPerStages from './includes/components/DisplayScoringPerStages';
import DisplayScoringPerDimensions from './includes/components/DisplayScoringPerDimensions';
import DisplayEvaluationSynthesis from './includes/components/DisplayEvaluationSynthesis';
import { Breadcrumb } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';

export default function CollaboratorScoreCard(props) {
	// mandatory basics
	const [url, SetUrl] = useState(null);
	const [languages, SetLanguages] = useState([]);

	// correspond aux scores catégories
	const [scoringPerCategories, SetScoringPerCategories] = useState(null);
	const [scoringPerSubCategories, SetScoringPerSubCategories] = useState(null);
	const [scoringPerSkills, SetScoringPerSkills] = useState(null);
	const [radarData, setRadarData] = useState(null);

	//correspond aux réponses de l'utilisateur
	const [answers, SetAnswers] = useState([]);

	const [analysis, setAnalysis] = useState(null);

	const getUrlAndLanguages = async () => {
		const response_url = await fetch(`/api/url/`);
		if (response_url.status === 200) {
			const data = await response_url.json();
			SetUrl('https://' + data);
		} else
			console.log(response_url);

		const response_language = await fetch(`/api/language/`);
		if (response_language.status === 200) {
			const data = await response_language.json();
			SetLanguages(data);
		} else
			console.log(response_language);
	};

	const transformCategories = (categories) => {
		// Récupère les clés et itère sur les catégories
		return Object.keys(categories).map((key) => {
			const category = categories[key];
			return {
				key: key,
				label: category.name,
				value: category.score,
				color: category.color,
				type: 'main',
				fake: 0,
			};
		});
	};

	const getAllScores = async () => {
		const response = await fetch(`/api/all-collaborator-scores/`);
		if (response.status === 200) {
			const data = await response.json();
			SetScoringPerCategories(data['categories']);
			SetScoringPerSubCategories(data['subcategories']);
			SetScoringPerSkills(data['skills']);
			setRadarData({
				society: '',
				type: 'mixity_evaluation_scan',
				footprint_type: 'standard',
				global: data['global']['score'],
				measures: transformCategories(data['categories']),
			});
		} else
			console.log(response);
	};

	const getAllAnswers = async () => {
		const response = await fetch(`/api/answer/`);
		if (response.status === 200) {
			const data = await response.json();
			SetAnswers(data);
		} else
			console.log(response);
	};

	const getIAAnalysis = async () => {
		const response = await fetch('/api/ia-scan-analysis/');
		if (response.status === 200) {
			const data = await response.json();
			setAnalysis(data);
		} else {
			console.log(response);
		}
	}

	useEffect(() => {
		getUrlAndLanguages();
		getAllScores();
		getAllAnswers();
		getIAAnalysis();
	}, [props]);

	return (
		<div style={{ fontFamily: 'DM Sans' }}>
			<style type="text/css">
				{`
                    .arrow-down {
                        transform: rotate(0deg);
                        transform: scale(1.2);
                        margin-top: 4px;
                        margin-left: 13px !important;
                    }

                    .arrow-up {
                        transform: rotate(180deg);
                        margin-bottom: 2px;
                    }
                    .arrow-down, .arrow-up {
                        transition: transform 0.3s;
                    }
                    .button-container {
                        display: flex;
                        flex-wrap: wrap;
                      }
                      .assess_white_btn, .assess_secondary_btn {
                        white-space: normal !important;
                      }
				`}
			</style>
			{/* Dashboard Header */}
			<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom"
				 style={{ backgroundColor: '#fff' }}>
				<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
					<Breadcrumb.Item href={'/non-adp'}>{gettext('Accueil')}</Breadcrumb.Item>
					<Breadcrumb.Item active>{gettext('Mesurer')}</Breadcrumb.Item>
					<Breadcrumb.Item active>
						<strong>{gettext('Mixity Scan')}</strong>
					</Breadcrumb.Item>
				</Breadcrumb>
				<Header
					data={{
						//TODO : modifier l'URL à récupérer
						url: 'https://localhost:8080/',
						languages: languages,
						language_code: language_code,
						enabled_website_languages: enabled_website_languages,
					}}
				/>
			</div>
			<div className="p-4 mt-4">
				<div className="row m-3 justify-content-between">
					{radarData &&
						<DisplayScanFootPrint data={{ radarData: radarData }} />
					}
					<DisplayProfile />
				</div>
				{/* <DisplayEvaluationSynthesis /> */}
				<div className="row mx-3 mt-5">
					<h3 className="mxt--large-bold">{gettext('Mon scan')}</h3>
					{/* TODO ajouter le benchmark */}
					<div>
						<DisplaySkills data={{ skills: scoringPerSkills }} />
						<DisplayScoringPerStages data={{ subcategories: scoringPerSubCategories, benchmark: false }} />
						<DisplayScoringPerDimensions data={{ categories: scoringPerCategories, answers: answers, analysis: analysis }} />
					</div>
				</div>
			</div>
		</div>
	);
}

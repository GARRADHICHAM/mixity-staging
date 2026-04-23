import React, { useState, useEffect } from 'react';
import { Card, Tabs, Tab } from 'react-bootstrap';
import AssessCategoryScore from '../../includes/AssessCategoryScore';
import DisplayFeedbackAnswers from './DisplayFeedbackAnswers';
import DisplayIAScanAnalysis from './DisplayIAScanAnalysis';

export default function DisplayScoringPerDimensions(props) {
	const [scoringPerDimensions, setScoringPerDimensions] = useState({});
	const [currentDimensionSlug, setCurrentDimensionSlug] = useState("");
	const [answers, setAnswers] = useState("");
	const [currentAnalysis, setCurrentAnalysis] = useState(null);
	const [analysis, setAnalysis] = useState(null);

	const globalScoresDescItem = (color, value) => {
		return (
			<div className="d-inline-flex align-items-center mb-1">
				<div className="me-2">
					<div className="indic-score" style={{ backgroundColor: `${color}`, width: '12px', height: '12px', borderRadius: '50%' }}></div>
				</div>
				<span className="mxt--small-bold">{gettext(value)}</span>
			</div>
		);
	};

	useEffect(() => {
		if (props.data.categories && props.data.answers) {
			setAnswers(props.data.answers);
			setScoringPerDimensions(props.data.categories);
			setCurrentDimensionSlug(Object.keys(props.data.categories)[0]);
			if (props.data.analysis) {
				setAnalysis(props.data.analysis)
				setCurrentAnalysis(props.data.analysis[Object.keys(props.data.categories)[0]])
			}
		}
	}, [props.data.categories, props.data.answers, props.data.analysis]);

	if (!scoringPerDimensions || !currentDimensionSlug) {
		return <div></div>;
	}

	const handleTabClick = (dimensionSlug) => {
		setCurrentDimensionSlug(dimensionSlug);
		setCurrentAnalysis(analysis[dimensionSlug])
	};

	return (
		<div className="mt-4">
			{/* Onglets par dimension (category) */}
			<Tabs
				defaultActiveKey={currentDimensionSlug}
				onSelect={handleTabClick}
				id="assess-tabs"
				className="nav-tabs mb-3"
			>
				{Object.entries(scoringPerDimensions).map(([slug, dimension], key) => {
					const isActive = currentDimensionSlug === slug;
					return (
						<Tab
							tabClassName={`nav-color nav-color-${slug}`}
							key={slug}
							eventKey={slug}
							title={
								<span style={{ color: isActive ? `--color-${slug}` : 'inherit' }}>
									{globalScoresDescItem(dimension.color, dimension.name, isActive)}
								</span>
							}
						>
							{/* Score par dimension (category) + benchmark à venir */}
							<Card style={{ borderRadius: '25px' }} className="mt-3">
								<Card.Body className="assess_global_scores justify-content-between">
									<div className="d-flex flex-column">
										<h3 className="fw-medium">{gettext('Score Dimension')}</h3>
										<Card.Text
											style={{
												fontSize: '14px',
												marginTop: '10px',
											}}
										>
											{gettext(dimension.name)}
										</Card.Text>
									</div>
									<div className="d-flex" style={{ width: '30%' }}>
										<AssessCategoryScore
											innerPercent={Math.round(dimension.score)}
											innerColor={dimension.color}
											benchmark={false}
										/>
									</div>
									<span className="d-flex m-4">{globalScoresDescItem(dimension.color, 'Vous', isActive)}</span>
								</Card.Body>
							</Card>
						</Tab>
					);
				})}
			</Tabs>
			{props.data.analysis && (currentAnalysis.strength.length > 0 || currentAnalysis.weakness.length > 0 || currentAnalysis.aim.length > 0) && (
				<DisplayIAScanAnalysis data={{analysis: currentAnalysis, category: currentDimensionSlug}} />
			)}
			<DisplayFeedbackAnswers data={{answers:answers.filter(answer => answer.category === currentDimensionSlug)}}/>
		</div>
	);
}

import React from 'react';
import { Card } from 'react-bootstrap';
import { CircularProgressbar, CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';

export default class GlobalScores extends React.Component {
	constructor(props) {
		super(props);
		this.state = { alpha: [0.3, 0.6, 1] };
	}

	componentDidMount() {
		if (this.props.data.scoresCategories === '') {
			this.props.data.scoresCategories = {
				mean_score_in_business_line: 50,
				mean_score: 50,
				value: 50,
			};
			this.setState({ alpha: [0.5, 0.5, 0.5] });
		}
	}

	convertToRGB(hexa, alpha) {
		hexa = hexa.slice(1);
		if (hexa.length != 6) {
			return 'rgba(255, 255, 255, 0.1)';
		}

		var aRgbHex = hexa.match(/.{1,2}/g);
		var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)},${alpha})`;
		return aRgb;
	}

	render() {
		// Récupération des données de scores
		const { category, scoresCategories } = this.props.data;
		if (!category)
			return <></>

		// Vérification des valeurs de scores
		const meanScoreInBusinessLine = isNaN(scoresCategories.mean_score_in_business_line) ? 50 : scoresCategories.mean_score_in_business_line;
		const meanScore = isNaN(scoresCategories.mean_score) ? 50 : scoresCategories.mean_score;
		const value = isNaN(scoresCategories.value) ? 50 : scoresCategories.value;

		return (
			<Card className="score__card p-3 m-2 border" style={{ backgroundColor: `${this.state.alpha[2] === 1 ? '#fff' : 'rgba(136, 136, 226, 0.1)'}` }}>
				<Card.Body className="px-0 py-2 text-center">
					<Card.Title className="score__title" style={{ color: `${this.convertToRGB(category.color, this.state.alpha[2])}` }}>
						{gettext(category.name)}
					</Card.Title>
					<div className="px-4 py-3 mb-2">
						{/* CircularProgressbarWithChildren pour le score */}
						<CircularProgressbarWithChildren
							value={meanScoreInBusinessLine}
							strokeWidth={3}
							styles={buildStyles({
								rotation: 0.5,
								pathColor: this.convertToRGB(category.color, this.state.alpha[0]),
								trailColor: 'rgba(240, 243, 255, 1)',
							})}
						>
							<div className="score__stroke">
								{/* CircularProgressbarWithChildren pour le score moyen */}
								<CircularProgressbarWithChildren
									value={meanScore}
									strokeWidth={3}
									styles={buildStyles({
										rotation: 0.5,
										pathColor: this.convertToRGB(category.color, this.state.alpha[1]),
										trailColor: 'rgba(240, 243, 255, 1)',
									})}
								>
									<div className="score__stroke">
										{/* CircularProgressbarWithChildren pour la valeur */}
										<CircularProgressbarWithChildren
											value={value}
											strokeWidth={8}
											styles={buildStyles({
												rotation: 0.5,
												pathColor: this.convertToRGB(category.color, this.state.alpha[2]),
												trailColor: 'rgba(240, 243, 240, 1)',
											})}
										>
											{/* Affichage du pourcentage */}
											<Card.Text
												className="score__percentage m-0"
												style={{ color: `${this.convertToRGB(category.color, this.state.alpha[2])}` }}
											>
												<b>{Math.round(value)}%</b>
											</Card.Text>
										</CircularProgressbarWithChildren>
									</div>
								</CircularProgressbarWithChildren>
							</div>
						</CircularProgressbarWithChildren>
					</div>
					<div className="px-3 row">
						{/* Affichage du score moyen dans le secteur */}
						<div className="d-flex flex-column w-50 p-0">
							<h6 className="score__subtitle p-0 m-0">{gettext('Secteur')}</h6>
							<div className="d-flex flex-row justify-content-evenly">
								<div className="score__smallCircle">
									<CircularProgressbar
										value={100}
										strokeWidth={12}
										styles={buildStyles({
											pathColor: this.convertToRGB(category.color, this.state.alpha[1]),
										})}
									/>
								</div>
								<h6 className="score__smallPercentage p-0 m-0">{Math.round(meanScore)} %</h6>
							</div>
						</div>
						{/* Affichage du score moyen global */}
						<div className="d-flex flex-column w-50 p-0">
							<h6 className="score__subtitle p-0 m-0">{gettext('Global')}</h6>
							<div className="d-flex flex-row justify-content-evenly">
								<div className="score__bigCircle">
									<CircularProgressbar
										value={100}
										strokeWidth={12}
										styles={buildStyles({
											pathColor: this.convertToRGB(category.color, this.state.alpha[0]),
										})}
									/>
								</div>
								<h6 className="score__smallPercentage p-0 m-0">{Math.round(meanScoreInBusinessLine)} %</h6>
							</div>
						</div>
					</div>
				</Card.Body>
			</Card>
		);
	}
}

import React, { Component } from 'react';

export default class GapChart extends Component {
	constructor(props) {
		super(props);
	}

	closestValue(x) {
		const liste = [0, 1, 3, 5, 10, 15];
		let closestValue = 0;
		let diffMin = Math.abs(x - closestValue);

		for (let i = 1; i < liste.length; i++) {
			const difference = Math.abs(x - liste[i]);
			if (difference < diffMin) {
				diffMin = difference;
				closestValue = liste[i];
			}
		}

		if (x < 0) return closestValue * -1;
		else return closestValue;
	}

	gapBarsHF(value) {
		const sizeMap = {
			15: { sizeF: 255, sizeH: 300 },
			10: { sizeF: 270, sizeH: 300 },
			5: { sizeF: 285, sizeH: 300 },
			3: { sizeF: 290, sizeH: 300 },
			1: { sizeF: 295, sizeH: 300 },
			0: { sizeF: 300, sizeH: 300 },
			'-1': { sizeF: 300, sizeH: 300 },
			'-3': { sizeF: 300, sizeH: 295 },
			'-5': { sizeF: 300, sizeH: 290 },
			'-10': { sizeF: 300, sizeH: 285 },
			'-15': { sizeF: 300, sizeH: 270 },
		};

		// const numericValue = parseFloat(value);

		const sizeInfo = sizeMap[this.closestValue(value).toString()];

		// Utiliser les valeurs de taille par défaut si aucune correspondance n'est trouvée
		var sizeF = 300;
		var sizeH = 300;
		if (sizeInfo) {
			sizeF = sizeInfo.sizeF;
			sizeH = sizeInfo.sizeH;
		}

		return (
			<div>
				<div className="d-flex align-items-end">
					<div className="bar m-2" style={{ height: sizeH + 'px', backgroundColor: '#FF6F6F' }}></div>
					<div className="bar m-2" style={{ height: sizeF + 'px', backgroundColor: '#994343' }}></div>
				</div>
			</div>
		);
	}

	valueorND(value) {
		if (value) {
			if (value > 10 || value < -10) return Math.round(value);
			else return value.toFixed(2);
		} else return 0;
	}

	render() {
		return (
			<React.Fragment>
				{this.props.labels.map((label, index) => {
					return (
						<div className="w-100 d-flex justify-content-center">
							<div className="d-grid w-100" style={{ gridTemplateColumns: '40% 60%' }}>
								<div className="d-flex align-items-center justify-content-end p-0">{this.gapBarsHF(this.props.data[0].data[index])}</div>
								<div className="d-flex flex-column align-items-center justify-content-end flex-wrap">
									<div className="circularChart_legend d-flex align-items-center flex-wrap h-25">
										<div className="d-inline-flex align-items-center py-2 me-3">
											<div>
												<div className="indic-score pe-2" style={{ backgroundColor: '#FF6F6F' }}></div>
											</div>
											<span className="legend_value">{gettext('Hommes')}</span>
										</div>
										<div className="d-inline-flex align-items-center py-2">
											<div>
												<div className="indic-score pe-2" style={{ backgroundColor: '#994343' }}></div>
											</div>
											<span className="legend_value">{gettext('Femmes')}</span>
										</div>
									</div>
									<div className="d-flex h-50 justify-content-center align-items-center">
										<p className="m-0 pt-3">
											<span className="fw-bold" style={{ fontSize: '30px' }}>
												{Math.abs(this.valueorND(this.props.data[0].data[index]))}
											</span>
											<React.Fragment>
												{this.valueorND(this.props.data[0].data[index]) > 0 ? (
													<span>
														{
															<b className="fw-bold" style={{ fontSize: '30px' }}>
																%{' '}
															</b>
														}
														{gettext('en faveur des hommes')}
													</span>
												) : (
													<span>
														{
															<b className="fw-bold" style={{ fontSize: '30px' }}>
																%{' '}
															</b>
														}
														{gettext('en faveur des femmes')}
													</span>
												)}
											</React.Fragment>
										</p>
									</div>
									{this.props.labels.length > 1 && (
										<div className="circularChart_legend d-flex align-items-center justify-content-end h-25">
											<span className="fw-bold">{label}</span>
										</div>
									)}
								</div>
							</div>
						</div>
					);
				})}
			</React.Fragment>
		);
	}
}

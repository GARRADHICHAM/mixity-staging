import React, { Component } from 'react';
import { getColors } from './ColorData';

export default class GapChart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			activeIndex: 0,
			activeBenchmark: false,
		};
	}

	gapBars(values, colors, isMeanscore) {
		var sizeF = 300;
		var sizeH = 300;

		if (Math.round(values[0]) > Math.round(values[1])) sizeH = 270;
		else if (Math.round(values[0]) < Math.round(values[1])) sizeF = 270;

		return (
			<div>
				{isMeanscore ? (
					<div className="d-flex align-items-end">
						<div className="bar m-1" style={{ height: sizeF / 2, width: '20px', backgroundColor: colors[0] }}></div>
						<div className="bar m-1" style={{ height: sizeH / 2, width: '20px', backgroundColor: colors[1] }}></div>
					</div>
				) : (
					<div className="d-flex align-items-end">
						<div className="bar m-2" style={{ height: sizeF + 'px', width: '40px', backgroundColor: colors[0] }}></div>
						<div className="bar m-2" style={{ height: sizeH + 'px', width: '40px', backgroundColor: colors[1] }}></div>
					</div>
				)}
			</div>
		);
	}

	closestValue(x) {
		const liste = [-15, -10, -5, -3, -1, 0, 1, 3, 5, 10, 15];
		let closestValue = 0;
		let diffMin = Math.abs(x - closestValue);

		for (let i = 1; i < liste.length; i++) {
			const difference = Math.abs(x - liste[i]);
			if (difference < diffMin) {
				diffMin = difference;
				closestValue = liste[i];
			}
		}

		return closestValue;
	}

	gapBarsHF(value, colors, isMeanscore) {
		const sizeMap = {
			15: { sizeF: 255, sizeH: 300 },
			10: { sizeF: 270, sizeH: 300 },
			5: { sizeF: 285, sizeH: 300 },
			3: { sizeF: 290, sizeH: 300 },
			1: { sizeF: 295, sizeH: 300 },
			0: { sizeF: 300, sizeH: 300 },
			'-1': { sizeF: 300, sizeH: 295 },
			'-3': { sizeF: 300, sizeH: 290 },
			'-5': { sizeF: 300, sizeH: 285 },
			'-10': { sizeF: 300, sizeH: 270 },
			'-15': { sizeF: 300, sizeH: 255 },
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
				{isMeanscore ? (
					<div className="d-flex align-items-end">
						<div className="bar m-1" style={{ height: sizeF / 2, width: '20px', backgroundColor: colors[0] }}></div>
						<div className="bar m-1" style={{ height: sizeH / 2, width: '20px', backgroundColor: colors[1] }}></div>
					</div>
				) : (
					<div className="d-flex align-items-end">
						<div className="bar m-2" style={{ height: sizeF + 'px', width: '40px', backgroundColor: colors[0] }}></div>
						<div className="bar m-2" style={{ height: sizeH + 'px', width: '40px', backgroundColor: colors[1] }}></div>
					</div>
				)}
			</div>
		);
	}

	valueorND(index, values_to_check) {
		if (this.props.data.selector && values_to_check[this.state.activeIndex].length > index) {
			if (Math.abs(values_to_check[this.state.activeIndex][index]) > 10)
				return Math.round(values_to_check[this.state.activeIndex][index]);
			else
				return values_to_check[this.state.activeIndex][index];
		} else if (!this.props.data.selector && values_to_check.length > index) {
			if (Math.abs(values_to_check[index]) > 10)
				return Math.round(values_to_check[index]);
			else
				return values_to_check[index];
		} else
			return gettext("Cette donnée n'est pas disponible");
	}

	meanscoresRender(datas, meanscoreType, simpleGap) {
		var title = gettext('Moyenne secteur');
		if (meanscoreType === 'meanscore_global_list') title = gettext('Moyenne globale');
		if (simpleGap) {
			return (
				<div className="d-grid w-100" style={{ gridTemplateColumns: '40% 60%' }}>
					<div className="d-flex align-items-center justify-content-center p-0">
						{this.gapBarsHF(
							this.props.data.selector ? datas[this.state.activeIndex][0] : datas[0],
							getColors(meanscoreType, this.props.data.colors),
							true,
						)}
					</div>
					<div className="d-flex flex-column align-items-center justify-content-center flex-wrap">
						<div className="d-flex h-50">
							<p className="m-0 pt-3">
								<span className="fw-bold" style={{ fontSize: '24px' }}>
									{this.valueorND(0, datas) == gettext("Cette donnée n'est pas disponible") ? (
										this.valueorND(0, datas)
									) : (
										<>
											{Math.abs(this.valueorND(0, datas))}
											{' '}
											{this.props.data.display_params.ending}
											{' '}
										</>
									)}
								</span>
								{!this.props.data.display_params.ending && (
									<React.Fragment>
										{this.valueorND(0, datas) > 0 ? (
											<span>
												{!this.props.data.display_params.ending && (
													<b className="fw-bold" style={{ fontSize: '30px' }}>
														%{' '}
													</b>
												)}
												{gettext('en faveur des hommes')}
											</span>
										) : (
											this.valueorND(0, datas) < 0 ? (
												<span>
													{!this.props.data.display_params.ending && (
														<b className="fw-bold" style={{ fontSize: '30px' }}>
															%{' '}
														</b>
													)}
													{gettext('en faveur des femmes')}
												</span>
											) : (
												<span>
													<b className="fw-bold" style={{ fontSize: '30px' }}>
														%
													</b>
												</span>
											)
										)}
									</React.Fragment>
								)}
							</p>
						</div>
						<p className="legend_value d-flex justify-content-center">{title}</p>
						<div className="circularChart_legend d-flex justify-content-center align-items-end flex-wrap h-50">
							<div className="d-inline-flex align-items-center py-2 me-3">
								<div>
									<div
										className="indic-score pe-2"
										style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[0]}` }}
									></div>
								</div>
								<span className="legend_value">{gettext('Femmes')}</span>
							</div>
							<div className="d-inline-flex align-items-center py-2">
								<div>
									<div
										className="indic-score pe-2"
										style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[1]}` }}
									></div>
								</div>
								<span className="legend_value">{gettext('Hommes')}</span>
							</div>
						</div>
					</div>
				</div>
			);
		} else {
			return (
				<div>
					<div className="d-grid align-items-center" style={{ gridTemplateColumns: '33% 33% 33%', justifyItems: 'center' }}>
						<div className="d-flex">
							<p>
								<span className="fw-bold" style={{ fontSize: '24px' }}>
									{this.valueorND(0, datas)}{' '}
									{this.valueorND(0, datas) != gettext("Cette donnée n'est pas disponible") && this.props.data.display_params.ending}
								</span>
							</p>
						</div>
						<div className="d-flex align-items-center p-0">{this.gapBars(datas, getColors(meanscoreType, this.props.data.colors), true)}</div>
						<div className="d-flex">
							<p>
								<span className="fw-bold" style={{ fontSize: '24px' }}>
									{this.valueorND(1, datas)}{' '}
									{this.valueorND(1, datas) != gettext("Cette donnée n'est pas disponible") && this.props.data.display_params.ending}
								</span>
							</p>
						</div>
					</div>
					{!this.props.data.id === 20236038 ? (
						<div>
							<p className="legend_value d-flex justify-content-center">{title}</p>
							<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
								<div className="d-inline-flex align-items-center py-2 me-3">
									<div>
										<div
											className="indic-score me-2"
											style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[0]}` }}
										></div>
									</div>
									<span className="legend_value">{gettext('Femmes')}</span>
								</div>
								<div className="d-inline-flex align-items-center py-2">
									<div>
										<div
											className="indic-score me-2"
											style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[1]}` }}
										></div>
									</div>
									<span className="legend_value">{gettext('Hommes')}</span>
								</div>
							</div>
						</div>
					) : (
						<div>
							<p className="legend_value d-flex justify-content-center">{title}</p>
							<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
								<div className="d-inline-flex align-items-center py-2 me-3">
									<div>
										<div
											className="indic-score me-2"
											style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[0]}` }}
										></div>
									</div>
									<span className="legend_value">{gettext(this.props.data.labels[0])}</span>
								</div>
								<div className="d-inline-flex align-items-center py-2">
									<div>
										<div
											className="indic-score me-2"
											style={{ backgroundColor: `${getColors(meanscoreType, this.props.data.colors)[1]}` }}
										></div>
									</div>
									<span className="legend_value">{gettext(this.props.data.labels[1])}</span>
								</div>
							</div>
						</div>
					)}
				</div>
			);
		}
	}

	render() {
		return (
			<React.Fragment>
				{this.props.data.selector && (
					<select
						className="select_indicator mb-3"
						name="selectedSubquestion"
						defaultValue="0"
						onChange={(e) => this.setState({ activeIndex: e.target.value })}
					>
						{this.props.data.selector_labels.map((label, index) => {
							return (
								<option key={index} value={`${index}`}>
									{label}
								</option>
							);
						})}
					</select>
				)}
				{this.props.data.perimeter && (
					<h4 className="w-100 fw-medium text-center mb-4" style={{ fontWeight: '400', fontSize: '12px' }}>
						{this.props.data.perimeter}
					</h4>
				)}
				<div className="w-100 d-flex justify-content-center">
					{(this.props.data.selector && this.props.data.values[0] && this.props.data.values[0].length > 1) ||
					(!this.props.data.selector && this.props.data.values && this.props.data.values.length > 1) ? (
						<div className="w-100">
							<div className="d-flex justify-content-between">
								<div className={`${this.state.activeBenchmark ? 'w-50' : 'w-100'}`}>
									<div className="d-grid align-items-center" style={{ gridTemplateColumns: '33% 33% 33%', justifyItems: 'center' }}>
										<div className="d-flex">
											<p>
												<span className="fw-bold" style={{ fontSize: '30px' }}>
													{this.valueorND(0, this.props.data.values)}{' '}
													{this.valueorND(0, this.props.data.values) != gettext("Cette donnée n'est pas disponible") &&
														this.props.data.display_params.ending}
												</span>
											</p>
										</div>
										<div className="d-flex align-items-center p-0">
											{this.gapBars(this.props.data.values, getColors(this.props.category + '_list', this.props.data.colors), false)}
										</div>
										<div className="d-flex">
											<p>
												<span className="fw-bold" style={{ fontSize: '30px' }}>
													{this.valueorND(1, this.props.data.values)}{' '}
													{this.valueorND(1, this.props.data.values) != gettext("Cette donnée n'est pas disponible") &&
														this.props.data.display_params.ending}
												</span>
											</p>
										</div>
									</div>
									{!this.props.data.id === 20236038 ? (
										<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
											<div className="d-inline-flex align-items-center py-2 me-3">
												<div>
													<div
														className="indic-score me-2"
														style={{ backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[0]}` }}
													></div>
												</div>
												<span className="legend_value">{gettext('Femmes')}</span>
											</div>
											<div className="d-inline-flex align-items-center py-2">
												<div>
													<div
														className="indic-score me-2"
														style={{ backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[1]}` }}
													></div>
												</div>
												<span className="legend_value">{gettext('Hommes')}</span>
											</div>
										</div>
									) : (
										<div className="circularChart_legend d-flex justify-content-center align-items-center flex-wrap mt-3">
											<div className="d-inline-flex align-items-center py-2 me-3">
												<div>
													<div
														className="indic-score me-2"
														style={{ backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[0]}` }}
													></div>
												</div>
												<span className="legend_value">{gettext(this.props.data.labels[0])}</span>
											</div>
											<div className="d-inline-flex align-items-center py-2">
												<div>
													<div
														className="indic-score me-2"
														style={{ backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[1]}` }}
													></div>
												</div>
												<span className="legend_value">{gettext(this.props.data.labels[1])}</span>
											</div>
										</div>
									)}
								</div>
								{this.state.activeBenchmark && (
									<div className="w-50 align-content-between">
										{/*SECTOR*/}
										{this.meanscoresRender(this.props.data.meanscore_sector_values, 'meanscore_sector_list', false)}
										{/*GLOBAL*/}
										{this.meanscoresRender(this.props.data.meanscore_global_values, 'meanscore_global_list', false)}
									</div>
								)}
							</div>
						</div>
					) : (
						<div className="w-100">
							<div className="d-flex justify-content-between">
								<div className={`${this.state.activeBenchmark ? 'w-50' : 'w-100'}`}>
									<div className="d-grid w-100" style={{ gridTemplateColumns: '40% 60%' }}>
										<div className="d-flex align-items-center justify-content-end p-0">
											{this.gapBarsHF(
												this.props.data.selector ? this.props.data.values[this.state.activeIndex][0] : this.props.data.values[0],
												getColors(this.props.category + '_list', this.props.data.colors),
											)}
										</div>
										<div className="d-flex flex-column align-items-center justify-content-center flex-wrap">
											<div className="d-flex h-50">
												<p className="m-0 pt-3">
													<span className="fw-bold" style={{ fontSize: '30px' }}>
														{this.valueorND(0, this.props.data.values) == gettext("Cette donnée n'est pas disponible") ? (
															this.valueorND(0, this.props.data.values)
														) : (
															<>
																{Math.abs(this.valueorND(0, this.props.data.values))}
																{' '}
																{this.props.data.display_params.ending}
																{' '}
															</>
														)}
													</span>
													{!this.props.data.display_params.ending && (
														<React.Fragment>
															{this.valueorND(0, this.props.data.values) > 0 ? (
																<span>
																	{!this.props.data.display_params.ending && (
																		<b className="fw-bold" style={{ fontSize: '30px' }}>
																			%{' '}
																		</b>
																	)}
																	{gettext('en faveur des hommes')}
																</span>
															) : (
																this.valueorND(0, this.props.data.values) < 0 ? (
																	<span>
																		{!this.props.data.display_params.ending && (
																			<b className="fw-bold" style={{ fontSize: '30px' }}>
																				%{' '}
																			</b>
																		)}
																		{gettext('en faveur des femmes')}
																	</span>
																) : (
																	<span>
																		<b className="fw-bold" style={{ fontSize: '30px' }}>
																			%
																		</b>
																	</span>
																)
															)}
														</React.Fragment>
													)}
												</p>
											</div>
											<div className="circularChart_legend d-flex justify-content-center align-items-end flex-wrap h-50">
												<div className="d-inline-flex align-items-center py-2 me-3">
													<div>
														<div
															className="indic-score pe-2"
															style={{
																backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[0]}`,
															}}
														></div>
													</div>
													<span className="legend_value">{gettext('Femmes')}</span>
												</div>
												<div className="d-inline-flex align-items-center py-2">
													<div>
														<div
															className="indic-score pe-2"
															style={{
																backgroundColor: `${getColors(this.props.category + '_list', this.props.data.colors)[1]}`,
															}}
														></div>
													</div>
													<span className="legend_value">{gettext('Hommes')}</span>
												</div>
											</div>
										</div>
									</div>
								</div>
								{this.state.activeBenchmark && (
									<div className="w-50 align-content-between">
										{/*SECTOR*/}
										{this.meanscoresRender(this.props.data.meanscore_sector_values, 'meanscore_sector_list', true)}
										{/*GLOBAL*/}
										{this.meanscoresRender(this.props.data.meanscore_global_values, 'meanscore_global_list', true)}
									</div>
								)}
							</div>
						</div>
					)}
				</div>
				<React.Fragment>
					<div className="d-flex gap-2 justify-content-center align-items-center my-3">
						<div className="d-flex align-items-center">
							<input
								type="checkbox"
								id={`input-filter-${this.props.data.title}`}
								value={this.state.activeBenchmark}
								onClick={() => this.setState({ activeBenchmark: !this.state.activeBenchmark })}
							></input>
							<label className="ps-2">{gettext('Afficher le Benchmark')}</label>
						</div>
					</div>
				</React.Fragment>
			</React.Fragment>
		);
	}
}

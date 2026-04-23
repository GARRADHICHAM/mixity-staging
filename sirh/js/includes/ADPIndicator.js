import React, { useEffect, useRef, useState } from 'react';
import { Form } from 'react-bootstrap';
import CircularChart from '../indicators/CircularChart';
import { BarChart } from '../indicators/BarChart';
import { PieChart } from '../indicators/PieChart';
import { LineChart } from '../indicators/LineChart';
import GapChart from '../indicators/GapChart';
import { getColors } from '../../../scoring/dashboard/js/includes/ColorData';

export function ADPIndicator(props) {
	const responseStatus = useRef(200);
	const [indicatorsData, setIndicatorsData] = useState(null); // list of indicators
	const [selectedIndicator, setSelectedIndicator] = useState(null); // current indicator
	const [selectedFilter, setSelectedFilter] = useState(null); // selected primary filter
	const [selectedSecondaryFilter, setSelectedSecondaryFilter] = useState(null); // selected secondaryFilter
	const [selectedFilterSecondaryFilters, setSelectedFilterSecondaryFilters] = useState(null); // list of secondary filters available for current primary filter
	const [displayThirdFilter, setDisplayThirdFilter] = useState(false); // labels : by key series label / data label, "series" by serie
	const [thirdFilterData, setThirdFilterData] = useState(null); // list of boolean. The index corresponds to the index of the filter

	useEffect(() => {
		// We load current indicator. Name corresponds to ADPIndicatorType
		fetch(`../api/indicator-retrieve/${props.name}/`)
			.then((response) => {
				responseStatus.current = response.status;
				if (response.status >= 400) {
					indicatorsData.current = false;
					return {};
				}
				return response.json();
			})
			.then((data) => {
				if (responseStatus.current < 400) {
					setIndicatorsData(data);
				}
			});
	}, []);

	useEffect(() => {
		if (indicatorsData !== null) {
			let index = Object.keys(indicatorsData.indicators).indexOf('global');
			if (index === -1) index = 0;
			changeFilter(index);
		}
	}, [indicatorsData]);
	// on load, we select the first primary filter. Might change it to "Global" by default instead of the first one

	function changeFilter(index) {
		if (indicatorsData !== null && indicatorsData.filters[0]) {
			const s = indicatorsData.filters[index];
			setSelectedFilter(s.key);
			setDisplayThirdFilter(s.third_filter || false); // we only add a third filter (checkboxes) if requested in the indicator data
			if (indicatorsData.filters[0].secondary_filters !== undefined) {
				// some indicators have secondary filters (age for instance). We add a second dropdown for those.
				const ss = indicatorsData.filters[index].secondary_filters;
				setSelectedFilterSecondaryFilters(ss);
				setSelectedSecondaryFilter(ss[0]);
				setSelectedIndicator(indicatorsData.indicators[s.key][ss[0]]);
				if (s.third_filter) {
					initThirdFilter(indicatorsData.indicators[s.key][ss[0]]);
				}
			} else {
				setSelectedIndicator(indicatorsData.indicators[s.key]);
				if (s.third_filter) {
					initThirdFilter(indicatorsData.indicators[s.key], s.third_filter);
				}
			}
		}
	}

	function initThirdFilter(indicator, thirdFilter = true) {
		// By default, the third filter only selects the first checkbox
		let data = null;
		let elem = [];
		if (indicator.data !== undefined) {
			data = indicator.data;
		} else {
			if (thirdFilter === 'series') {
				data = indicator.series;
			} else {
				data = indicator.labels;
			}
		}
		data.forEach((e, i) => {
			elem.push(i === 0);
		});
		setThirdFilterData(elem);
	}

	function changeThirdFilterStatus(index) {
		// when we check/uncheck a third filter, we edit the current state of the third filter. (true = checked, false = unchecked)
		let elem = [...thirdFilterData];
		elem[index] = !elem[index];
		let checked = false;
		elem.forEach((e) => {
			checked = e || checked;
		});
		if (checked) setThirdFilterData(elem);
	}

	// we filter labels/series by values of third filter (if thirdFilter[3] is true, then elements[3] will be kept)
	function getFilteredLabels(elements) {
		if (displayThirdFilter === 'labels') return elements.filter((e, i) => thirdFilterData[i]); // we only filter labels when we precisely ask for it
		return elements;
	}

	// same as before but with data
	function getFilteredData(series) {
		if (thirdFilterData) {
			if (displayThirdFilter === 'series') {
				return series.filter((e, i) => thirdFilterData[i]); // for cases of multiple indicators or when we have multiple series on one indicator
			} else if (displayThirdFilter === 'labels') {
				// when we have certain type of data on a simple indicator such as gender, job, ...
				const seriesClone = [...series];
				seriesClone.forEach((e, i) => {
					seriesClone[i] = { ...e };
					seriesClone[i].data = seriesClone[i].data.filter((e, i) => thirdFilterData[i]);
				});
				return seriesClone;
			}
		}
		return series;
	}
	function getThirdFilter() {
		if (displayThirdFilter === 'series') return selectedIndicator?.data || selectedIndicator?.series;
		return selectedIndicator?.labels;
	}

	function changeSecondaryFilter(index) {
		setSelectedSecondaryFilter(selectedFilterSecondaryFilters[index]);
		setSelectedIndicator(indicatorsData.indicators[selectedFilter][selectedFilterSecondaryFilters[index]]);
	}

	if (selectedIndicator && props.activeCategory === props.category) {
		return (
			<div className="d-flex flex-column card" style={{ padding: '2rem', margin: '1rem', width: '47%', borderRadius: '25px' }}>
				<h3 className="fw-medium text-center mb-4">{selectedIndicator && selectedIndicator.title}</h3>
				<div className="d-flex justify-content-around">
					{indicatorsData?.filters ? (
						<select className="select_indicator mb-3" style={{ width: 'auto' }} onChange={(e) => changeFilter(e.target.selectedIndex)}>
							{indicatorsData?.filters.map((e, i) => {
								return <option selected={e.key === selectedFilter}>{e.name}</option>;
							})}
						</select>
					) : (
						''
					)}
					{selectedFilterSecondaryFilters ? (
						<select className="select_indicator mb-3" style={{ width: 'auto' }} onChange={(e) => changeSecondaryFilter(e.target.selectedIndex)}>
							{selectedFilterSecondaryFilters?.map((e, i) => {
								return <option selected={selectedSecondaryFilter === e}>{e}</option>;
							})}
						</select>
					) : (
						''
					)}
				</div>

				{displayThirdFilter ? (
					<React.Fragment>
						<div
							className="d-flex justify-content-center flex-wrap m-3 p-3 w-100"
							style={{ backgroundColor: '#F6F7FB', borderRadius: '10% / 50%' }}
						>
							{getThirdFilter()?.map((e, i) => {
								return (
									<div key={i}>
										<Form.Check
											type="checkbox"
											id={`input-filter-${props.name}-${i}`}
											checked={thirdFilterData[i]}
											label={e.label || e}
											className={`d-flex align-items-center collab_filter my-3 mx-2`}
											onChange={() => changeThirdFilterStatus(i)}
										/>
									</div>
								);
							})}
							<div
								className="d-flex align-items-center collab_filter my-3 mx-2"
								style={{ border: 'none', backgroundColor: 'trasnparent', cursor: 'pointer' }}
								onClick={() => initThirdFilter(selectedIndicator)}
							>
								<i className="fa fa-trash" style={{ color: '#181B3D' }}></i>
							</div>
						</div>
					</React.Fragment>
				) : (
					''
				)}
				{selectedIndicator ? (
					selectedIndicator.indicator_type === 'MultiplePieChart' ? (
						<div>
							<div className="w-100 d-flex justify-content-center">
								{selectedIndicator.data[0].labels.map((label, index) => {
									return (
										<div key={index} className="d-inline-flex align-items-center py-2 pe-3">
											<div>
												<div className="indic-score" style={{ backgroundColor: `${getColors('gender_list', [2, 3, 5])[index]}` }}></div>
											</div>
											<span className="legend_value">{label}</span>
										</div>
									);
								})}
							</div>
							<div className="w-100 d-flex flex-wrap justify-content-center align-items-center">
								{getFilteredData(selectedIndicator.data).map((e) => {
									return (
										<div style={{ width: '47%' }}>
											<PieChart labels={e.labels} data={e.series} title={e.label} />
										</div>
									);
								})}
							</div>
						</div>
					) : // for now we only get first 5 elements for testing purposes
					selectedIndicator.indicator_type === 'MultipleHorizontalBarChart' ? ( // for now we use this indicator
						<div>
							<div className="w-100 d-flex justify-content-center">
								{[gettext('Femmes'), gettext('Hommes'), gettext('Non-binaires')].map((label, index) => {
									return (
										<div key={index} className="d-inline-flex align-items-center py-2 pe-3">
											<div>
												<div
													className="indic-score"
													style={{ backgroundColor: `${getColors('generational_diversity_list', [1, 3, 5])[index]}` }}
												></div>
											</div>
											<span className="legend_value">{label}</span>
										</div>
									);
								})}
							</div>
							<div className="d-flex flex-wrap mb-3">
								{getFilteredData(selectedIndicator.data).map((e) => {
									return <BarChart labels={e.labels} data={e.series} title={e.label} axis="y" />;
								})}
							</div>
						</div>
					) : // for now we only get first 5 elements for testing purposes
					selectedIndicator.indicator_type === 'GapChart' ? (
						<div className="w-100 d-flex flex-column align-items-center justify-content-evenly">
							<GapChart labels={getFilteredLabels(selectedIndicator.labels)} data={getFilteredData(selectedIndicator.series)} />
						</div>
					) : selectedIndicator.indicator_type === 'HorizontalBarChart' ? (
						<BarChart labels={getFilteredLabels(selectedIndicator.labels)} data={getFilteredData(selectedIndicator.series)} axis="y" />
					) : selectedIndicator.indicator_type === 'CircularChart' ? (
						<div className="w-100 d-flex flex-column align-items-center justify-content-evenly">
							<CircularChart data={getFilteredData(selectedIndicator.data)} color={selectedIndicator.color} />
						</div>
					) : selectedIndicator.indicator_type === 'LineChart' ? (
						<LineChart
							data={getFilteredData(selectedIndicator.series)}
							labels={getFilteredLabels(selectedIndicator.labels)}
							color={selectedIndicator.color}
						/>
					) : (
						''
					)
				) : (
					gettext('Chargement en cours')
				)}
			</div>
		);
	}
}

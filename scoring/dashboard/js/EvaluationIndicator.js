import React, { useEffect, useRef, useState, Component } from 'react';
import CircularChart from './includes/CircularChart';
import ScanCircularChart from './includes/ScanCircularChart';
import GapChart from './includes/GapChart';
import ProgressBarChart from './includes/ProgressBarChart';
import TextChart from './includes/TextChart';
import CheckListIndicator from './includes/ChecklistIndicator';
import BarChart from './includes/BarChart';
import ScanBarChart from './includes/ScanBarChart';
import PieChart from './includes/PieChart';
import LineChart from './includes/LineChart';
import MultipleBarChart from './includes/MultipleBarChart';

// Donnée absente (liste vide, null ou chaîne vide) : même message pour tous les types de graphique.
const NOT_AVAILABLE = gettext("Cette donnée n'est pas disponible");
const hasIndicatorData = (values) =>
	[]
		.concat(values ?? [])
		.flat(Infinity)
		.some((v) => v !== null && v !== undefined && v !== '' && !(typeof v === 'number' && isNaN(v)));

class AssessIndicators extends Component {
	constructor(props) {
		super(props);
		this.state = {
			indicatorList: {
				PieChart: (selectedIndicator) => (
					<PieChart
						title={selectedIndicator.title}
						data={selectedIndicator}
						category={props.category}
						isCriteria={props.isCriteria}
						isHuman={this.props.isHuman}
					/>
				),
				BarChart: (selectedIndicator) => (
					<BarChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
				),
				ScanBarChart: (selectedIndicator) => (
					<ScanBarChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
				),
				MultipleBarChart: (selectedIndicator) => (
					<MultipleBarChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
				),
				CircularChart: (selectedIndicator) => (
					<div className="d-flex flex-column align-items-center flex-wrap w-100" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
						<CircularChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
					</div>
				),
				ScanCircularChart: (selectedIndicator) => (
					<div className="d-flex flex-column align-items-center flex-wrap w-100" style={{ marginTop: '1rem', marginBottom: '1rem' }}>
						<ScanCircularChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
					</div>
				),
				LineChart: (selectedIndicator) => (
					<LineChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
				),
				GapChart: (selectedIndicator) => (
					<div className="w-100 d-flex flex-column align-items-center justify-content-evenly">
						<GapChart title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
					</div>
				),
				ProgressBarChart: (selectedIndicator) => (
					<div className="w-100">
						<ProgressBarChart
							title={selectedIndicator.title}
							data={selectedIndicator}
							category={props.category}
							isCriteria={props.isCriteria}
							isHuman={this.props.isHuman}
						/>
					</div>
				),
				TextChart: (selectedIndicator) => (
					<div className="w-100">
						<TextChart
							title={selectedIndicator.title}
							data={selectedIndicator}
							category={props.category}
							svg={props.svg}
							isHuman={this.props.isHuman}
						/>
					</div>
				),
				CheckListIndicator: (selectedIndicator) => (
					<div className="d-flex flex-column align-items-center justify-content-start w-100">
						<CheckListIndicator title={selectedIndicator.title} data={selectedIndicator} category={props.category} isHuman={this.props.isHuman} />
					</div>
				),
			},
			selectedIndicator: '',
		};
	}
	render() {
		let componentContent;
		let title;
		if (this.props.json) {
			var width = '47%';
			if (this.props.json.display_params.size === 2) width = '97%';
			if (this.state.indicatorList[this.props.json.indicator_type]) {
				title = this.props.json.label ? this.props.json.label : this.props.json.title;
				componentContent = hasIndicatorData(this.props.json.values) ? (
					<div className="d-flex justify-content-center flex-wrap w-100 flex-grow-1">
						{this.state.indicatorList[this.props.json.indicator_type](this.props.json)}
					</div>
				) : (
					<p className="text-center text-muted w-100 my-4">{NOT_AVAILABLE}</p>
				);
			} else {
				title = this.props.json.label ? this.props.json.label : this.props.json.title;
				componentContent = <div key={this.props.index}>Indicator not found for element {this.props.index}</div>;
			}
		} else {
			componentContent = <div>{gettext('Chargement en cours')}</div>;
		}

		return this.props.json.indicator_type === 'TextChart' ? (
			<div
				className={`d-flex flex-column ${
					!this.props.json.display_params.linked_with || this.props.json.display_params.linked_with.length < 2 ? 'card' : ''
				}`}
				style={
					!this.props.json.display_params.linked_with || this.props.json.display_params.linked_with.length < 2
						? { padding: '2rem', margin: '1rem', width: width, borderRadius: '25px' }
						: { width: '47%' }
				}
			>
				<div className={'d-flex justify-content-start'}>
					{this.props.json.display_params.linked_with.length < 2 && this.props.json.display_params.svg && (
						<div style={{ width: '7%', marginRight: '2em' }}>
							<img src={'/static/img/textChart/' + this.props.json.display_params.svg} />
						</div>
					)}
					{componentContent}
				</div>
			</div>
		) : this.props.json.indicator_type === 'MultipleBarChart' ? (
			<div className="d-flex flex-column">
				<h3 className="fw-medium text-center mb-4">{title}</h3>
				{componentContent}
			</div>
		) : this.props.json.indicator_type === 'ProgressBarChart' && this.props.isCriteria ? (
			<div className={'d-flex flex-column card'} style={{ width: '48%', borderRadius: '25px' }}>
				<h3 className="fw-medium text-center mb-4">{title}</h3>
				{componentContent}
			</div>
		) : (
			<div
				className={`d-flex flex-column ${
					this.props.json.display_params.linked_with && this.props.json.display_params.linked_with.length >= 2 ? '' : 'card'
				}`}
				style={
					!this.props.json.display_params.linked_with || this.props.json.display_params.linked_with.length < 2
						? { padding: '2rem', margin: '1rem', width: width, borderRadius: '25px' }
						: { width: '47%' }
				}
			>
				<h3 className="fw-medium text-center mb-4">{title}</h3>
				{this.props.isHuman && this.props.json.indicator_type === 'CircularChart' && (
					<h4 className="fw-medium text-center mb-4" style={{ fontWeight: '400', fontSize: '12px' }}>
						{gettext('Taux de personnes ayant répondu oui')}
					</h4>
				)}
				{this.props.isScan && this.props.json.indicator_type === 'ScanCircularChart' && (
					<h4 className="fw-medium text-center mb-4" style={{ fontWeight: '400', fontSize: '12px' }}>
						{gettext('Taux de bonnes réponses')}
					</h4>
				)}
				{componentContent}
			</div>
		);
	}
}

export default AssessIndicators;

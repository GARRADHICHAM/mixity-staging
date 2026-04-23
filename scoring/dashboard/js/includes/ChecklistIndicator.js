import React, { Component } from 'react';
import { getColors } from './ColorData';

export default class CheckListIndicator extends Component {
	constructor(props) {
		super(props);
		this.state = {
			activeTab: true,
			done: [],
			toDo: [],
		};
	}

	componentDidMount() {
		var done = [];
		var toDo = [];

		if (this.props.data.selector) {
			this.props.data.values[0].map((value, index) => {
				if (value) done.push(this.props.data.labels[0][index]);
				else toDo.push(this.props.data.labels[0][index]);
			});
		} else {
			this.props.data.values.map((value, index) => {
				if (value) done.push(this.props.data.labels[index]);
				else toDo.push(this.props.data.labels[index]);
			});
		}
		this.setState({
			done: done,
			toDo: toDo,
		});
	}

	changeDatas(e) {
		e.preventDefault();
		var done = [];
		var toDo = [];

		this.props.data.values[e.target.value].map((value, index) => {
			if (value) done.push(this.props.data.labels[e.target.value][index]);
			else toDo.push(this.props.data.labels[e.target.value][index]);
		});

		this.setState({
			done: done,
			toDo: toDo,
		});
	}

	render() {
		return (
			<React.Fragment>
				<div className="d-flex flex-column justify-content-center align-items-center w-100">
					{this.props.data.selector && (
						<select className="select_indicator mb-3" name="selectedSubquestion" defaultValue="0" onChange={(e) => this.changeDatas(e)}>
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
					<div
						className="d-flex justify-content-center mt-3 mb-4"
						style={{ backgroundColor: getColors(this.props.category + '_list', [5]), borderRadius: '50px', width: 'fit-content' }}
					>
						<label>
							<button
								className="py-3 px-4"
								style={{
									backgroundColor: `${this.state.activeTab ? getColors(this.props.category + '_list', [3]) : getColors(this.props.category + '_list', [5])}`,
									border: 'none',
									borderRadius: '50px',
									width: 'fit-content',
								}}
								type="button"
								onClick={() => this.setState({ activeTab: true })}
							>
								<span className="fw-medium color--primary-dark">{gettext('En place')}</span>
							</button>
							<button
								className="py-3 px-4"
								style={{
									backgroundColor: `${this.state.activeTab ? getColors(this.props.category + '_list', [5]) : getColors(this.props.category + '_list', [3])}`,
									border: 'none',
									borderRadius: '50px',
									width: 'fit-content',
								}}
								type="button"
								onClick={() => this.setState({ activeTab: false })}
							>
								<span className="fw-medium color--primary-dark">{gettext('À mettre en place')}</span>
							</button>
						</label>
					</div>
				</div>
				<div className="flex-wrap justify-content-center align-items-start w-100">
					{this.state.activeTab
						? this.state.done.map((label) => (
								<div className="d-flex align-items-center py-2 w-100" key={label}>
									<div className="pe-2" style={{ width: '9%' }}>
										<img src={'/static/img/disk-check.svg'} />
									</div>
									<div style={{ width: '91%' }}>{label}</div>
								</div>
							))
						: this.state.toDo.map((label) => (
								<div className="d-flex align-items-center py-2 w-100" key={label}>
									<div className="pe-2" style={{ width: '9%' }}>
										<img src={'/static/img/circle-remove.svg'} />
									</div>
									<div style={{ width: '91%' }}>{label}</div>
								</div>
							))}
				</div>
			</React.Fragment>
		);
	}
}

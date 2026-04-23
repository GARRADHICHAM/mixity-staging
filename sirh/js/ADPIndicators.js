import React, { Component, createRef } from 'react';
import { Breadcrumb, Modal } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';
import { ADPIndicator } from './includes/ADPIndicator';

class ADPIndicators extends Component {
	constructor(props) {
		super(props);
		this.state = {
			url: '',
			indicators: [],
			error: false,
			loading: true,
			activeCategory: 'governance',
		};
	}

	componentDidMount() {
		// We load the list of indicators available for the current entity. /!\ For testing purposes, the list might be filtered because all indicators are not yet done. Check the backend.
		fetch('../api/indicators-list/')
			.then((response) => {
				this.setState({ loading: false });
				if (response.status >= 400) {
					return this.setState(() => {
						return {
							placeholder: gettext("Quelque chose s'est mal passé !"),
							error: true,
						};
					});
				}
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						indicators: data,
					};
				});
			});
	}

	activateCategory(category) {
		this.setState({ activeCategory: category });
	}

	render() {
		return this.state.error ? (
			<h4 className="d-flex justify-content-center align-items-middle">{gettext("Quelque chose s'est mal passé")}</h4>
		) : this.state.loading ? (
			<h4 className="d-flex justify-content-center align-items-middle">{gettext('Chargement en cours...')}</h4>
		) : (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item color="inherit" active>
							{gettext('Mesurer')}
						</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('ADP')}</Breadcrumb.Item>
					</Breadcrumb>
					<Header
						data={{
							url: this.state.url,
							languages: languages,
							language_code: language_code,
							enabled_website_languages: enabled_website_languages,
						}}
					/>
				</div>
				<div className="nav nav-tabs d-flex justify-content-start" id="nav-tab" role="tablist">
					{[
						{ slug: 'governance', name: gettext('Gouvernance'), color: '#8888E2' },
						{ slug: 'movement', name: gettext('Mouvements'), color: '#FF7070' },
						{ slug: 'remuneration', name: gettext('Rémunération'), color: '#03A87C' },
					].map((category, index) => {
						return (
							<button
								key={index}
								data-bs-toggle="tab"
								className={`nav-link ${index === 0 ? 'active' : ''}`}
								style={{ borderBottomColor: `${category.color}`, borderWidth: '0 0 2px 0', color: `${category.color}` }}
								onClick={() => this.activateCategory(category.slug)}
							>
								{gettext(category.name)}
							</button>
						);
					})}
				</div>
				<div className="d-flex justify-content-center flex-wrap w-100 flex-grow-1">
					{this.state.indicators.map((e) => {
						return <ADPIndicator {...e} activeCategory={this.state.activeCategory} />;
					})}
				</div>
			</div>
		);
	}
}

export default ADPIndicators;

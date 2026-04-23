import React, { Component } from 'react';
import { Breadcrumb, Card, Tab, Tabs, Modal, Form } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import NotificationLoader from '../../../mixity/dashboard/js/includes/NotificationLoader';
import AssessCategoryScore from './includes/AssessCategoryScore';
import AssessSubCategoryScore from './includes/AssessSubCategoryScore';
import AssessSubCategoryScoreSkeletonLoader from './includes/AssessSubCategoryScoreSkeletonLoader';
import AssessCategoryScoreSkeletonLoader from './includes/AssessCategoryScoreSkeletonLoader';
import AssessIndicators from './EvaluationIndicator';
import StrengthsAndWeaknesses from './includes/StrengthsAndWeaknesses';

import DisplayFootprint from './includes/components/DisplayFootprint';
import DisplayDownloads from './includes/components/DisplayDownloads';
import ShowMoreCharacteristics from './includes/components/ShowMoreCharacteristics';
import DisplayEvaluationSynthesis from './includes/components/DisplayEvaluationSynthesis';

import NamsorIndicator from '../../../theme/src/js/indicators/NamsorIndicator';

import { Skeleton } from '@mui/material';

import { getColors } from './includes/ColorData';
import { date } from '../../../theme/src/js/jszip';
import DisplayScoringPerStages from './includes/components/DisplayScoringPerStages';
import DisplayDataRepartitionBySkills from './includes/components/DisplayDataRepartitionBySkills';
import DisplayProfileRepartition from './includes/components/DisplayProfileRepartition';

class AssessPage extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to /api/url/ request
			url: '',
			urlEvaluation: '',

			//related to /api/entity/ request
			entity: {},
			entity_struct: {},
			structure: {},
			entityLoaded: false,

			//related to /api/language/ request
			languages: [],
			enabled_lang: [],
			google_sheet_lang: [],
			languagesLoaded: false,

			//related to /api/membership/ request
			is_owner: false,
			is_reader: false,
			is_staff: false,
			user_id: null,

			//related to /api/assess-evaluation/ request
			evaluation: null,
			radarData: null,
			evaluationLoaded: false,
			evaluationStarted: false,
			global_score_delta: 0,
			mean_score_in_business_line: 0,
			mean_score: 0,

			//related to /api/api_evaluations-versions-list/ request
			versionsList: [],

			//related to /api/subscription-option
			product: '',
			isSubscriptionCurrent: false,
			productLoaded: false,

			//related to /api/human-form-choices/ request
			defaultFormChoices: {},
			humanCriteriaFormChoices: {},
			defaultFormInputs: {},
			humanCriteriaFormInputs: {},
			formChoicesLoaded: false,
			human_selected_filters: {},
			activeMainFormTab: '',
			activeChildFormTab: '',
			defaultChilfFormTab: '',

			//related to /api/human-collaborators-count/ request
			nbAnswers: 0,
			nbCollaborators: 0,
			nbCollaboratorsWithFilterMin: 0,
			nbWorkforceTotal: 0,
			nbCollaboratorsTotal: 0,
			nbWorkforceLoaded: false,
			nbAnswersLoaded: false,
			nbCollaboratorsLoaded: false,

			//related to /api/assess-score-categories/ request
			scoreCategories: [],
			scoreCategoriesLoaded: false,
			currentCategoryScore: {},
			currentCategoryScoreLoaded: false,
			defaultCategoryScore: {},
			tabsCategories: [],
			tabsCategoriesLoaded: false,
			currentCategorySlug: '',

			//realted to /api/indicator/ request
			Indicators: {},
			Indicatorsloaded: false,
			linkedWithList: [],

			//related to /api/PK/subcategory-scores/ request
			currentSubcategoryScore: {},
			currentSubcategoryScoreLoaded: false,
			firstcurrentSubcategoryScoreLoaded: false,

			//related to /api/human-collaborators-infos/
			CollaboratorsIndicators: {},
			AgeDistribution: {},
			CivilityDistribution: {},
			HumanCollaboratorInfoLoaded: false,
			DefaultHumanCollaboratorFilter: '{"default":{"age":[],"civility":[]},"human_criteria":[]}',
			showCollaboratorsIndicators: false,
			appliedForm: false,

			//related to api/diag-caracteristics/
			DiagCaracteristicsInfo: {},
			DiagCaracteristicsLoaded: false,

			//related to /api/general-analysis/
			synthesis: {},

			//related to /api/comments/
			CommentsLoaded: false,

			//default var
			sub_score_catergory_filters: {
				default: { age: [], civility: [], status: [] },
				human_criteria: [],
			},
			placeholder: gettext('Chargement'),
			showForm: false,
			showChildForm: false,
			isDiagPage: false,
			isHumanPage: false,
			isScanPage: false,
			pdfactualfilter: '{"default":{"age":[],"civility":[]},"human_criteria":[]}',

			// gestion design toast pour les reeavaluations requests
			notification_is_active: false,

			// related to namsor indicator
			namsorIndicatorContent: null,

			showIndicators: false,

			dimensions_infos: {
				"general_concept": [gettext("Cette dimension permet d’évaluer la maturité des répondants sur leur niveau de connaissance des notions en lien avec la non-discrimination au recrutement et le cadre réglementaire. Elle est déterminante dans les pratiques de recrutement inclusif au quotidien."), gettext("Exemple : connaissance du nombre de critères de discriminations définis par la loi.")],
				"professional_practice": [gettext("Cette dimension permet d’évaluer la maturité des répondants sur leur pratiques professionnelles, en lien avec les outils et pratiques attendues au quotidien en matière de recrutement inclusif."), gettext("Exemple : utilisation de grilles d’entretien, rédaction inclusive d’offres d’emploi…")],
				"cognitive_biases": [gettext("Cette dimension permet d’évaluer la maturité des répondants sur leur capacité à identifier et déjouer leurs biais cognitifs, stéréotypes et préjugé qui peuvent avoir un impact direct sur la discrimination à l’embauche."), gettext("Exemple : s’assurer de déjouer ses biais en situation de recrutement d’une personne qui déclare un handicap invisible.")],
				"communication": [gettext("Cette dimension permet d’évaluer la maturité des répondants sur leur capacité à communiquer de manière inlcusive, en tenant compte des singularités des candidats et candidates et à démonter une ouverture à la différence."), gettext("Exemple : posture à adopter avec une personne que vous recevez en entretien et qui parle avec une fort accent, qui rend difficile la fluidité des échanges.")],
				"professional_engagement": [gettext("Cette dimension permet d’évaluer la maturité des répondants sur leur ouverture, leur engagement individuel et leur curiosité concernant les sujets de diversité et d’inclusion. Cela s’inscrit dans le cadre professionnel et vient interroger les événements et temps forts de sensibilisation ou d’événements auxquels le répondant participe au sein de l’entreprise et sa capacité à être allié et/ou sponsor de l'inclusion en interne."), gettext("Exemple : participation à des temps de sensibilisation proposés par l’entreprise sur les sujets de diversité et d’inclusion.")],
			}
		};
	}

	isElement = (obj) => obj instanceof HTMLElement || obj instanceof SVGElement;
	requireDomNode = (el) => {
		if (!this.isElement(el)) throw new Error(`an HTMLElement or SVGElement is required; got ${el}`);
	};
	requireDomNodePromise = (el) =>
		new Promise((resolve, reject) => {
			if (this.isElement(el)) resolve(el);
			else reject(new Error(`an HTMLElement or SVGElement is required; got ${el}`));
		});

	// Wait for the DOM content to be loaded
	getFootprintSVG = () => {
		// Select the div with the class "radar"
		const radarDiv = document.querySelector('.radar');

		// Return a promise to handle the asynchronous setTimeout
		return new Promise((resolve, reject) => {
			setTimeout(() => {
				const generatedSVG = radarDiv.getElementsByTagName('svg')[0];
				resolve(generatedSVG);
			}, 0);
		});
	};

	isExternal = (url) => url && url.lastIndexOf('http', 0) === 0 && url.lastIndexOf(window.location.host) === -1;

	inlineImages = (el) =>
		Promise.all(
			Array.from(el.querySelectorAll('image')).map((image) => {
				let href = image.getAttributeNS('http://www.w3.org/1999/xlink', 'href') || image.getAttribute('href');
				if (!href) return Promise.resolve(null);
				if (this.isExternal(href)) {
					href += (href.indexOf('?') === -1 ? '?' : '&') + 't=' + new Date().valueOf();
				}
				return new Promise((resolve, reject) => {
					const canvas = document.createElement('canvas');
					const img = new Image();
					img.crossOrigin = 'anonymous';
					img.src = href;
					img.onerror = () => reject(new Error(`Could not load ${href}`));
					img.onload = () => {
						canvas.width = img.width;
						canvas.height = img.height;
						canvas.getContext('2d').drawImage(img, 0, 0);
						image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', canvas.toDataURL('image/png'));
						resolve(true);
					};
				});
			}),
		);

	getDimension = (el, clone, dim) => {
		const v =
			(el.viewBox && el.viewBox.baseVal && el.viewBox.baseVal[dim]) ||
			(clone.getAttribute(dim) !== null && !clone.getAttribute(dim).match(/%$/) && parseInt(clone.getAttribute(dim))) ||
			el.getBoundingClientRect()[dim] ||
			parseInt(clone.style[dim]) ||
			parseInt(window.getComputedStyle(el).getPropertyValue(dim));
		return typeof v === 'undefined' || v === null || isNaN(parseFloat(v)) ? 0 : v;
	};

	getDimensions = (el, clone, width, height) => {
		if (el.tagName === 'svg') {
			return {
				width: width || this.getDimension(el, clone, 'width'),
				height: height || this.getDimension(el, clone, 'height'),
			};
		} else if (el.getBBox) {
			const { x, y, width, height } = el.getBBox();
			return {
				width: x + width,
				height: y + height,
			};
		}
	};

	prepareSvg = (el, options, done) => {
		this.requireDomNode(el);
		const { left = 0, top = 0, width: w, height: h, scale = 1, responsive = false } = options || {};

		return this.inlineImages(el).then(() => {
			let clone = el.cloneNode(true);
			clone.style.backgroundColor = (options || {}).backgroundColor || el.style.backgroundColor;
			const { width, height } = this.getDimensions(el, clone, w, h);

			if (el.tagName !== 'svg') {
				if (el.getBBox) {
					if (clone.getAttribute('transform') != null) {
						clone.setAttribute('transform', clone.getAttribute('transform').replace(/translate\(.*?\)/, ''));
					}
					const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
					svg.appendChild(clone);
					clone = svg;
				} else {
					console.error('Attempted to render non-SVG element', el);
					return;
				}
			}

			clone.setAttribute('version', '1.1');
			clone.setAttribute('viewBox', [left, top, width, height].join(' '));
			const xmlNs = 'http://www.w3.org/2000/xmlns/';
			const svgNs = 'http://www.w3.org/2000/svg';
			if (!clone.getAttribute('xmlns')) clone.setAttributeNS(xmlNs, 'xmlns', svgNs);
			if (!clone.getAttribute('xmlns:xlink')) clone.setAttributeNS(xmlNs, 'xmlns:xlink', 'http://www.w3.org/1999/xlink');

			if (responsive) {
				clone.removeAttribute('width');
				clone.removeAttribute('height');
				clone.setAttribute('preserveAspectRatio', 'xMinYMin meet');
			} else {
				clone.setAttribute('width', width * scale);
				clone.setAttribute('height', height * scale);
			}

			Array.from(clone.querySelectorAll('foreignObject > *')).forEach((foreignObject) => {
				foreignObject.setAttributeNS(xmlNs, 'xmlns', foreignObject.tagName === 'svg' ? svgNs : xhtmlNs);
			});

			return this.inlineCss(el, options).then((css) => {
				const style = document.createElement('style');
				style.setAttribute('type', 'text/css');
				style.innerHTML = `<![CDATA[\n${css}\n]]>`;

				const defs = document.createElement('defs');
				defs.appendChild(style);
				clone.insertBefore(defs, clone.firstChild);

				const outer = document.createElement('div');
				outer.appendChild(clone);
				const src = outer.innerHTML.replace(/NS\d+:href/gi, 'xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href');

				if (typeof done === 'function') done(src, width, height);
				else return { src, width, height };
			});
		});
	};

	styleSheetRules = () => {
		let cachedRules = null;
		if (cachedRules) return cachedRules;
		return (cachedRules = Array.from(document.styleSheets).map((sheet) => {
			try {
				return { rules: sheet.cssRules, href: sheet.href };
			} catch (e) {
				console.warn(`Stylesheet could not be loaded: ${sheet.href}`, e);
				return {};
			}
		}));
	};

	query = (el, selector) => {
		if (!selector) return;
		try {
			return el.querySelector(selector) || (el.parentNode && el.parentNode.querySelector(selector));
		} catch (err) {
			console.warn(`Invalid CSS selector "${selector}"`, err);
		}
	};

	getFontMimeTypeFromUrl = (fontUrl) => {
		const fontFormats = {
			woff2: 'font/woff2',
			woff: 'font/woff',
			otf: 'application/x-font-opentype',
			ttf: 'application/x-font-ttf',
			eot: 'application/vnd.ms-fontobject',
			sfnt: 'application/font-sfnt',
			svg: 'image/svg+xml',
		};
		const formats = Object.keys(fontFormats)
			.filter((extension) => fontUrl.indexOf(`.${extension}`) > 0)
			.map((extension) => fontFormats[extension]);
		if (formats) return formats[0];
		console.error(`Unknown font format for ${fontUrl}. Fonts may not be working correctly.`);
		return 'application/octet-stream';
	};

	detectCssFont = (rule, href) => {
		// Match CSS font-face rules to external links.
		// @font-face {
		//   src: local('Abel'), url(https://fonts.gstatic.com/s/abel/v6/UzN-iejR1VoXU2Oc-7LsbvesZW2xOQ-xsNqO47m55DA.woff2);
		// }
		const urlRegex = /url\(["']?(.+?)["']?\)/;
		const match = rule.cssText.match(urlRegex);
		const url = (match && match[1]) || '';
		if (!url || url.match(/^data:/) || url === 'about:blank') return;
		const fullUrl = url.startsWith('../') ? `${href}/../${url}` : url.startsWith('./') ? `${href}/.${url}` : url;
		return {
			text: rule.cssText,
			format: this.getFontMimeTypeFromUrl(fullUrl),
			url: fullUrl,
		};
	};

	arrayBufferToBase64 = (buffer) => {
		let binary = '';
		const bytes = new Uint8Array(buffer);
		for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
		return window.btoa(binary);
	};

	inlineFonts = (fonts) =>
		Promise.all(
			fonts.map(
				(font) =>
					new Promise((resolve, reject) => {
						const cachedFonts = {};
						if (cachedFonts[font.url]) return resolve(cachedFonts[font.url]);

						const req = new XMLHttpRequest();
						req.addEventListener('load', () => {
							// TODO: it may also be worth it to wait until fonts are fully loaded before
							// attempting to rasterize them. (e.g. use https://developer.mozilla.org/en-US/docs/Web/API/FontFaceSet)
							const fontInBase64 = this.arrayBufferToBase64(req.response);
							const urlRegex = /url\(["']?(.+?)["']?\)/;
							const fontUri = font.text.replace(urlRegex, `url("data:${font.format};base64,${fontInBase64}")`) + '\n';
							cachedFonts[font.url] = fontUri;
							resolve(fontUri);
						});
						req.addEventListener('error', (e) => {
							console.warn(`Failed to load font from: ${font.url}`, e);
							cachedFonts[font.url] = null;
							resolve(null);
						});
						req.addEventListener('abort', (e) => {
							console.warn(`Aborted loading font from: ${font.url}`, e);
							resolve(null);
						});
						req.open('GET', font.url);
						req.responseType = 'arraybuffer';
						req.send();
					}),
			),
		).then((fontCss) => fontCss.filter((x) => x).join(''));

	inlineCss = (el, options) => {
		const { selectorRemap, modifyStyle, modifyCss, fonts } = options || {};
		const generateCss =
			modifyCss ||
			((selector, properties) => {
				const sel = selectorRemap ? selectorRemap(selector) : selector;
				const props = modifyStyle ? modifyStyle(properties) : properties;
				return `${sel}{${props}}\n`;
			});
		const css = [];
		const detectFonts = typeof fonts === 'undefined';
		const fontList = fonts || [];
		this.styleSheetRules().forEach(({ rules, href }) => {
			if (!rules) return;
			Array.from(rules).forEach((rule) => {
				if (typeof rule.style !== 'undefined') {
					if (this.query(el, rule.selectorText)) css.push(generateCss(rule.selectorText, rule.style.cssText));
					else if (detectFonts && rule.cssText.match(/^@font-face/)) {
						const font = this.detectCssFont(rule, href);
						if (font) fontList.push(font);
					} else css.push(rule.cssText);
				}
			});
		});

		return this.inlineFonts(fontList).then((fontCss) => css.join('\n') + fontCss);
	};

	reEncode = (data) =>
		decodeURIComponent(
			encodeURIComponent(data).replace(/%([0-9A-F]{2})/g, (match, p1) => {
				const c = String.fromCharCode(`0x${p1}`);
				return c === '%' ? '%25' : c;
			}),
		);

	svgAsDataUri = (el, options, done) => {
		this.requireDomNode(el);
		return this.prepareSvg(el, options).then(({ src, width, height }) => {
			const doctype =
				'<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" [<!ENTITY nbsp "&#160;">]>';
			const svgXml = `data:image/svg+xml;base64,${window.btoa(this.reEncode(doctype + src))}`;
			if (typeof done === 'function') {
				done(svgXml, width, height);
			}
			return svgXml;
		});
	};

	svgAsPngUri = (el, options, done) => {
		this.requireDomNode(el);
		const { encoderType = 'image/png', encoderOptions = 0.8, canvg } = options || {};
		const convertToPng = ({ src, width, height }) => {
			const canvas = document.createElement('canvas');
			const context = canvas.getContext('2d');
			const pixelRatio = window.devicePixelRatio || 1;
			canvas.width = width * pixelRatio;
			canvas.height = height * pixelRatio;
			canvas.style.width = `${canvas.width}px`;
			canvas.style.height = `${canvas.height}px`;
			context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
			if (canvg) canvg(canvas, src);
			else context.drawImage(src, 0, 0);
			let png;
			try {
				png = canvas.toDataURL(encoderType, encoderOptions);
			} catch (e) {
				if ((typeof SecurityError !== 'undefined' && e instanceof SecurityError) || e.name === 'SecurityError') {
					console.error('Rendered SVG images cannot be downloaded in this browser.');
					return;
				} else throw e;
			}
			if (typeof done === 'function') done(png, canvas.width, canvas.height);
			return Promise.resolve(png);
		};
		if (canvg) {
			return this.prepareSvg(el, options).then(convertToPng);
		} else {
			return this.svgAsDataUri(el, options).then((uri) => {
				return new Promise((resolve, reject) => {
					const image = new Image();
					image.onload = () =>
						resolve(
							convertToPng({
								src: image,
								width: image.width,
								height: image.height,
							}),
						);
					image.onerror = () => {
						reject(
							`There was an error loading the data URI as an image on the following SVG\n${window.atob(
								uri.slice(26),
							)}Open the following link to see browser's diagnosis\n${uri}`,
						);
					};
					image.src = uri;
				});
			});
		}
	};

	saveToBackend = (eval_id, name, uri, upload_url, csrftoken) => {
		var formData = new FormData();
		formData.append('footprint', uri);
		formData.append('csrfmiddlewaretoken', csrftoken);
		var request = new XMLHttpRequest();
		// param false => synchrone => wait for awnser
		request.open('POST', upload_url, true);
		request.setRequestHeader('X-CSRFToken', csrftoken);
		request.send(formData);
	};

	updateFootprint = async () => {
		const svg = await this.getFootprintSVG();
		const options = {
			backgroundColor: '#1fe0',
		};
		const eval_id = this.state.evaluation.pk;
		const name = svg.id + '.png';
		const upload_url = '/scoring/evaluation/' + eval_id + '/footprint/upload/';
		return this.requireDomNodePromise(svg)
			.then((svg) => this.svgAsPngUri(svg, options || {}))
			.then((uri) => this.saveToBackend(eval_id, name, uri, upload_url, csrftoken))
			.then(alert('Empreinte mise à jour !'));
	};

	// Loading hook implementation
	async componentDidMount() {
		try {
			//  URL
			const response_url = await fetch('api/url/');
			this.fetchErrorMessage(response_url);
			const data_url = await response_url.json();

			let url = 'https://' + data_url;
			let url_evaluation = 'https://' + data_url;
			if (window.location.pathname.split('/').filter(Boolean)[0])
				url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/' + window.location.pathname.split('/').filter(Boolean)[1];
			const is_diag_page = window.location.href.includes('diag');
			const is_human_page = window.location.href.includes('human');
			const is_scan_page = window.location.href.includes('scan');

			let segments = window.location.pathname.split('/').filter(Boolean);
			let version_slug = segments[segments.length - 1];

			this.setState(() => {
				return {
					url: url,
					urlEvaluation: url_evaluation,
					isDiagPage: is_diag_page,
					isHumanPage: is_human_page,
					isScanPage: is_scan_page,
				};
			});
			const [response_entity, response_language, response_membership, response_evaluation, response_versions_list] = await Promise.all([
				fetch(this.state.urlEvaluation + '/api/entity/'),
				fetch(this.state.url + '/api/language/'),
				fetch(this.state.url + '/api/membership/'),
				fetch(this.state.urlEvaluation + '/api/assess-evaluation/' + version_slug),
				fetch(this.state.urlEvaluation + '/api/evaluations-versions-list/'),
			]);
			this.fetchErrorMessage(response_entity);
			this.fetchErrorMessage(response_language);
			this.fetchErrorMessage(response_membership);
			this.fetchErrorMessage(response_evaluation);
			this.fetchErrorMessage(response_versions_list);
			const [data_entity, data_languages, data_membership, data_evaluation, data_versions_list] = await Promise.all([
				response_entity.json(),
				response_language.json(),
				response_membership.json(),
				response_evaluation.json(),
				response_versions_list.json(),
			]);
			let radar_data = data_evaluation.get_radar_data;
			let new_measures = [];
			if (data_evaluation.is_scan) {
				new_measures.push(radar_data.measures[0]);
				radar_data.measures = new_measures.concat(radar_data.measures.slice(1).reverse());
			}
			this.setState(() => {
				return {
					// entity
					entity: data_entity[0],
					structure: data_evaluation.structure,
					entityLoaded: true,
					//language
					languages: data_languages,
					enabled_lang: Object.values(data_languages.filter((lang) => lang.is_enabled)),
					google_sheet_lang: Object.values(data_languages.filter((lang) => lang.is_google_sheet_lang)),
					languagesLoaded: true,
					//subscription
					is_owner: data_membership.is_owner,
					is_reader: data_membership.is_reader,
					is_staff: data_membership.is_staff,
					user_id: data_membership.user_id,
					// evaluation
					evaluation: data_evaluation,
					radarData: radar_data,
					evaluationLoaded: true,
					evaluationStarted: data_evaluation.is_started,
					storedScoreCategory: data_evaluation.scores_categories,
					global_score_delta: data_evaluation.get_global_score_delta,
					mean_score_in_business_line: data_evaluation.get_mean_score_in_business_line,
					mean_score: data_evaluation.get_mean_score,
					//version
					versionsList: data_versions_list,
				};
			});
			fetch(this.state.urlEvaluation + '/api/' + this.state.evaluation.pk + '/subscription-option')
				.then((response) => {
					if (response.status >= 400) {
						return context.setState(() => {
							return {
								placeholder: gettext("Quelque chose s'est mal passé !"),
							};
						});
					}
					return response.json();
				})
				.then((data) => {
					this.setState(() => {
						return {
							product: data.product,
							isSubscriptionCurrent: data.is_current,
							productLoaded: true,
						};
					});
				});

			fetch(this.state.urlEvaluation + '/api/general-analysis/')
				.then((response) => {
					if (response.status >= 400) {
						return context.setState(() => {
							return {
								placeholder: gettext("Quelque chose s'est mal passé !"),
							};
						});
					}
					return response.json();
				})
				.then((data) => {
					this.setState(() => {
						return {
							synthesis: data[0],
						};
					});
				});
			fetch(this.state.url + '/api/' + this.state.evaluation.pk + '/namsor-indicator-content/')
				.then((response) => {
					if (response.status != 200) {
						console.log('error with django namsor indicator content');
					}
					return response.json();
				})
				.then((data) => {
					this.setState(() => {
						return {
							namsorIndicatorContent: data,
						};
					});
				});
			// Human form choices
			if (this.state.evaluation.is_human || this.state.evaluation.is_scan) {
				const [response_form, response_counts] = await Promise.all([
					fetch(this.state.urlEvaluation + '/api/human-form-choices/'),
					fetch(this.state.urlEvaluation + '/api/human-collaborators-count/'),
				]);
				this.fetchErrorMessage(response_form);
				this.fetchErrorMessage(response_counts);
				const data_form = await response_form.json();
				const data_counts = await response_counts.json();
				const new_data_form = data_form['new'];
				const old_data_form = data_form['old'];
				var collaboratorsTotal = 0;
				if (this.state.evaluation.is_human) {
					collaboratorsTotal = this.state.evaluation.get_workforce_from_evaluation;
				} else {
					collaboratorsTotal = data_counts['nb_collaborator'];
				}
				this.setState(() => {
					return {
						// default
						defaultFormChoices: new_data_form['default'],
						// human criteria
						humanCriteriaFormChoices: new_data_form['human_criteria'],
						formChoicesLoaded: true,
						human_selected_filters: old_data_form,
						defaultFormInputs: this.createListFromKeys(Object.keys(new_data_form['default'])),
						humanCriteriaFormInputs: this.createListFromKeys(Object.keys(new_data_form['human_criteria'])),
						activeMainFormTab: `human_${Object.keys(new_data_form['default'])[0]}_form`,
						activeChildFormTab: `human_${Object.keys(new_data_form['human_criteria'])[0]}_form`,
						defaultChilfFormTab: `human_${Object.keys(new_data_form['human_criteria'])[0]}_form`,
						//answer
						nbAnswers: data_counts['nb_collaborator_answers'],
						nbCollaborators: this.state.evaluation.answer_count,
						nbCollaboratorsTotal: collaboratorsTotal,
						nbWorkforceTotal: this.state.evaluation.get_workforce_from_evaluation,
						nbCollaboratorsWithFilterMin: new_data_form['nb_collaborator_with_filter_min'],
						nbWorkforceLoaded: true,
						nbCollaboratorsLoaded: true,
						nbAnswersLoaded: true,
					};
				});
				let bodycontent = JSON.stringify(this.prepareFormInputs());
				this.getHumanCollaboratorInfo(bodycontent);
			} else {
				this.setState(() => {
					return {
						formChoicesLoaded: true,
					};
				});
			}
			await this.componentbodyMount();
			if (this.state.evaluation.public_display == true && this.state.evaluation.get_footprint_url == '') {
				await this.updateFootprint();
			}
		} catch (error) {
			console.error('>>>>> ERROR in assess evaluation : ', error);
		}
	}

	async componentbodyMount() {
		try {
			if (!this.state.evaluation.is_validated_by_admin) {
				return;
			}
			if (this.state.isHumanPage || this.state.isScanPage) this.getHumanCollaboratorInfo(this.state.DefaultHumanCollaboratorFilter);
			else if (this.state.isDiagPage) this.getDiagCaracteristics();
			// Global scores
			// Categories scores
			const response_cat_scores = await fetch(this.state.urlEvaluation + '/api/assess-score-categories/?eval_pk=' + this.state.evaluation.pk);
			this.fetchErrorMessage(response_cat_scores);
			const data_cat_scores = await response_cat_scores.json();
			let tabsCatList = [];
			JSON.parse(JSON.stringify(data_cat_scores)).map((score) => {
				tabsCatList.push(score.category);
			});
			this.setState(() => {
				return {
					scoreCategories: data_cat_scores,
					scoreCategoriesLoaded: true,
					defaultCategoryScore: data_cat_scores[0],
					tabsCategories: tabsCatList,
					tabsCategoriesLoaded: true,
					currentCategoryScore: data_cat_scores[0],
					currentCategorySlug: data_cat_scores[0].category.slug,
					currentCategoryScoreLoaded: true,
				};
			});
			this.getSubCategoryScores(data_cat_scores[0].pk, data_cat_scores[0].category.slug);
			// this.getComments();
			if (this.state.evaluation.is_human || this.state.evaluation.is_scan) {
				this.getHumanIndicator(this.state.currentCategorySlug, this.state.sub_score_catergory_filters);
			} else this.getDiagIndicator(this.state.currentCategorySlug);
		} catch (error) {
			console.error('>>>>> ERROR in assess page : ', error);
		}
	}

	// every function containing a fetch / request

	async refresh_entity_evaluation() {
		try {
			const [response_entity, response_evaluation] = await Promise.all([
				fetch(this.state.url + '/api/entity/'),
				fetch(this.state.urlEvaluation + '/api/assess-evaluation/' + version_slug),
			]);
			this.fetchErrorMessage(response_entity);
			this.fetchErrorMessage(response_evaluation);
			const [data_entity, data_evaluation] = await Promise.all([response_entity.json(), response_evaluation.json()]);
			this.setState(() => {
				return {
					// entity
					entity: data_entity[0],
					structure: data_evaluation.structure,
					entityLoaded: true,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in refresh entity evaluation : ', error);
		}
	}

	async getHumanIndicator(page, filter) {
		try {
			if (!this.state.Indicators[page] && (this.state.evaluation.is_human || this.state.evaluation.is_scan)) {
				if (this.state.evaluation.is_human) {
					const response_indicator = await fetch(
						`${this.state.urlEvaluation}/api/indicators/?page=${page}&eval_id=${this.state.evaluation.pk}&filter=${JSON.stringify(filter)}`,
					);
					this.fetchErrorMessage(response_indicator);
					var jsonHumanIndicator = await response_indicator.json();
				} else {
					const response_indicator = await fetch(
						`${this.state.urlEvaluation}/api/scan-indicators/?page=${page}&eval_id=${this.state.evaluation.pk}&filter=${JSON.stringify(filter)}`,
					);
					this.fetchErrorMessage(response_indicator);
					var jsonHumanIndicator = await response_indicator.json();
				}
				let updated_humanindicator = this.state.Indicators;
				updated_humanindicator[page] = jsonHumanIndicator;
				var linkedIds = [];
				jsonHumanIndicator.map((indicator) => {
					var duplicate = false;
					var canAdd = false;
					if (indicator.scores_json.display_params.linked_with) {
						var linked = indicator.scores_json.display_params.linked_with;
						linked.push(indicator.scores_json.id);
						linked = linked.sort();
						linkedIds.map((element) => {
							duplicate = element.every((element, index) => element === linked[index]);
							if (duplicate) canAdd = true;
						});
						if (!canAdd) linkedIds.push(linked);
					} else {
						linkedIds.push([indicator.scores_json.id]);
					}
				});
				this.setState(() => {
					return {
						Indicators: updated_humanindicator,
						Indicatorsloaded: true,
						linkedWithList: linkedIds,
					};
				});
			} else {
				var linkedIds = [];
				if (this.state.Indicators[page]) {
					this.state.Indicators[page].map((indicator) => {
						if (indicator.scores_json.display_params.linked_with) {
							if (
								indicator.scores_json.display_params.linked_with.length > 1 &&
								linkedIds.filter((element) => element.length === 2).length >= 1
							) {
								var duplicate = false;
								linkedIds.map((element) => {
									duplicate = element.every((element, index) => element === indicator.scores_json.display_params.linked_with[index]);
								});
								if (duplicate === false) linkedIds.push(indicator.scores_json.display_params.linked_with);
							} else linkedIds.push(indicator.scores_json.display_params.linked_with);
						}
					});
					this.setState(() => {
						return {
							Indicatorsloaded: true,
							linkedWithList: linkedIds,
						};
					});
				}
			}
		} catch (error) {
			console.error('>>>>> ERROR in assess page in function getHumanIndicator: ', error);
		}
	}

	async getDiagIndicator(page) {
		try {
			if (!this.state.Indicators[page] && !this.state.evaluation.is_human) {
				const response_indicator = await fetch(`${this.state.urlEvaluation}/api/indicators/?page=${page}&eval_id=${this.state.evaluation.pk}`);
				this.fetchErrorMessage(response_indicator);
				var jsonDiagIndicator = await response_indicator.json();
				let updated_diagindicator = this.state.Indicators;
				updated_diagindicator[page] = jsonDiagIndicator;
				let linkedIds = this.state.linkedWithList;
				jsonDiagIndicator.map((indicator) => {
					var duplicate = false;
					var canAdd = false;
					if (indicator.scores_json.display_params.linked_with) {
						var linked = indicator.scores_json.display_params.linked_with;
						linked.push(indicator.scores_json.id);
						linked = linked.sort();
						linkedIds.map((element) => {
							duplicate = element.every((element, index) => element === linked[index]);
							if (duplicate) canAdd = true;
						});
						if (!canAdd) linkedIds.push(linked);
					} else {
						linkedIds.push([indicator.scores_json.id]);
					}
				});
				this.setState(() => {
					return {
						Indicators: updated_diagindicator,
						Indicatorsloaded: true,
						linkedWithList: linkedIds,
					};
				});
			} else {
				this.setState(() => {
					return {
						Indicatorsloaded: true,
					};
				});
			}
		} catch (error) {
			console.error('>>>>> ERROR in assess page in function getDiagIndicator: ', error);
		}
	}

	// async getComments() {
	// 	try {
	// 		if (this.state.evaluation.is_diag) {
	// 			const response_comments = await fetch(`${this.state.urlEvaluation}/api/comments/`);
	// 			this.fetchErrorMessage(response_comments);
	// 			var comments = await response_comments.json();
	// 			var evaluation = this.state.evaluation;
	// 			comments.map((comment) => {
	// 				var com = {
	// 					description: comment.description,
	// 					category: comment.category.slug,
	// 					subcategory: comment.subcategory.name,
	// 				};
	// 				if (comment.is_good) evaluation.strengths.push(com);
	// 				else evaluation.weaknesses.push(com);
	// 			});
	// 			this.setState(() => {
	// 				return {
	// 					evaluation: evaluation,
	// 					CommentsLoaded: true,
	// 				};
	// 			});
	// 		} else {
	// 			this.setState(() => {
	// 				return {
	// 					CommentsLoaded: true,
	// 				};
	// 			});
	// 		}
	// 	} catch (error) {
	// 		console.error('>>>>> ERROR in assess page in function getComments: ', error);
	// 	}
	// }

	async getSubCategoryScores(pk, page, filtered = false) {
		try {
			if (!this.state.currentSubcategoryScore[page]) {
				const requestOptions = {
					credentials: 'include',
					method: filtered ? 'POST' : 'GET',
					headers: {
						'Content-Type': 'application/json;charset=utf-8',
					},
				};
				if (filtered) {
					requestOptions.headers['X-CSRFToken'] = csrftoken;
					let bodyOptions = this.prepareFormInputs();
					bodyOptions['score_cat_pk'] = pk;
					bodyOptions['product'] = this.state.product.slug;
					requestOptions.body = JSON.stringify(bodyOptions);
				}
				const response_filtered_subcat_scores = await fetch(`${this.state.urlEvaluation}/api/${pk}/subcategory-scores/`, requestOptions);
				this.fetchErrorMessage(response_filtered_subcat_scores);
				const data_filtered_subcat_scores = await response_filtered_subcat_scores.json();
				let updated_currentSubcategoryScore = this.state.currentSubcategoryScore;
				updated_currentSubcategoryScore[page] = data_filtered_subcat_scores['subcategories_scores'];
				this.setState(() => {
					return {
						currentSubcategoryScore: updated_currentSubcategoryScore,
						currentSubcategoryScoreLoaded: true,
					};
				});
			} else {
				this.setState(() => {
					return {
						currentSubcategoryScoreLoaded: true,
					};
				});
			}
		} catch (error) {
			console.error('>>>>> ERROR in assess page in function getSubCategoryScores: ', error);
		}
	}

	async getCollaboratorsCounts(requestOptions) {
		try {
			const response_filtered_collab_counts = await fetch(`${this.state.urlEvaluation}/api/human-collaborators-count/`, requestOptions);
			this.fetchErrorMessage(response_filtered_collab_counts);
			const data_filtered_collab_counts = await response_filtered_collab_counts.json();
			this.setState(() => {
				return {
					nbAnswers: data_filtered_collab_counts['nb_collaborator_answers_with_filters'],
					nbCollaborators: data_filtered_collab_counts['nb_collaborator_with_filters'],
					nbWorkforceTotal: data_filtered_collab_counts['get_workforce_from_evaluation_with_filters'],
					nbCollaboratorsLoaded: true,
					nbAnswersLoaded: true,
					nbWorkforceLoaded: true,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in assess page in function getCollaboratorsCounts: ', error);
		}
	}

	updatescorecategoryfiltered = async (requestOptions) => {
		try {
			const responseFilteredScoreCat = await fetch(`${this.state.urlEvaluation}/api/assess-score-categories/filtered_results_action/`, requestOptions);
			this.fetchErrorMessage(responseFilteredScoreCat);
			const dataFilteredScoreCat = await responseFilteredScoreCat.json();
			let currentSc = dataFilteredScoreCat['filtered_scores_categories'].find((sc) => sc.category.slug == this.state.currentCategorySlug);
			this.setState({
				scoreCategories: dataFilteredScoreCat['filtered_scores_categories'],
				currentCategoryScore: currentSc,
				currentCategorySlug: currentSc.category.slug,
				currentCategoryScoreLoaded: true,
				scoreCategoriesLoaded: true,
			});
		} catch (error) {
			console.error('>>>>>>>> ERROR in assess page in function updatescorecategoryfiltered : ', error);
		}
	};

	handleRequest = () => {
		// Mettre à jour l'état is_active à true
		this.setState({ notification_is_active: true });
	};

	handleRequestComplete = (isActive) => {
		this.setState({ notification_is_active: isActive });
	};

	async getHumanCollaboratorInfo(HumanCollaboratorInfofilter) {
		try {
			if (this.state.evaluation.is_human || this.state.evaluation.is_scan) {
				const responseHumanCollaboratorInfo = await fetch(
					`${this.state.urlEvaluation}/api/human-collaborators-infos/?filter=${HumanCollaboratorInfofilter}`,
				);
				this.fetchErrorMessage(responseHumanCollaboratorInfo);
				const dataHumanCollaboratorInfo = await responseHumanCollaboratorInfo.json();
				this.setState(() => {
					return {
						CollaboratorsIndicators: dataHumanCollaboratorInfo,
						HumanCollaboratorInfoLoaded: true,
						appliedForm: HumanCollaboratorInfofilter !== '{"default":{"age":[],"civility":[]},"human_criteria":[]}' ? true : false,
					};
				});
			} else {
				this.setState({
					HumanCollaboratorInfoLoaded: true,
				});
			}
		} catch (error) {
			console.error('>>>>>>>> ERROR in assess page in function getHumanCollaboratorInfo : ', error);
		}
	}

	async getDiagCaracteristics() {
		try {
			if (!this.state.evaluation.is_human && !this.state.evaluation.is_scan) {
				const responseDiagCaracteristics = await fetch(`${this.state.urlEvaluation}/api/diag-caracteristics/`);
				this.fetchErrorMessage(responseDiagCaracteristics);
				const dataDiagCaracteristics = await responseDiagCaracteristics.json();
				this.setState(() => {
					return {
						DiagCaracteristicsInfo: dataDiagCaracteristics,
						DiagCaracteristicsLoaded: true,
					};
				});
			} else {
				this.setState({
					DiagCaracteristicsLoaded: true,
				});
			}
		} catch (error) {
			console.error('>>>>>>>> ERROR in assess page in function getDiagCaracteristics : ', error);
		}
	}

	async getHumanRadarData(HumanInfofilter) {
		try {
			if (this.state.evaluation.is_human || this.state.evaluation.is_scan) {
				var meanscore = 0;
				const responseHumanRadarData = await fetch(`${this.state.urlEvaluation}/api/radar-data/?human_filter=${HumanInfofilter}`);
				this.fetchErrorMessage(responseHumanRadarData);
				const HumanRadarData = await responseHumanRadarData.json();
				for (var cv in HumanRadarData.measures) {
					meanscore += HumanRadarData.measures[cv].value;
				}
				meanscore = meanscore / HumanRadarData.measures.length;
				this.setState(() => {
					return {
						radarData: HumanRadarData,
						global_score_delta: meanscore,
						HumanCollaboratorInfoLoaded: true,
						appliedForm: HumanInfofilter !== '{"default":{"age":[],"civility":[]},"human_criteria":[]}' ? true : false,
					};
				});
			} else {
				this.setState({
					HumanCollaboratorInfoLoaded: true,
				});
			}
		} catch (error) {
			console.error('>>>>>>>> ERROR in assess page in function getHumanCollaboratorInfo : ', error);
		}
	}

	// Fetch Functions
	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return {
					placeholder: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
		return;
	}

	// change the score without reloading every value
	setCurrentScoreCategory(cat_slug) {
		if (this.state.scoreCategoriesLoaded && this.state.scoreCategories) {
			let score_cat = this.state.scoreCategories.find((sc) => sc.category.slug == cat_slug);
			this.setState(() => {
				return {
					currentCategoryScore: score_cat,
					currentCategoryScoreLoaded: true,
				};
			});
		}
	}

	handleActiveTab = async (key) => {
		await this.setState(() => {
			return {
				currentCategorySlug: key,
				currentCategoryScoreLoaded: false,
				currentSubcategoryScoreLoaded: false,
				Indicatorsloaded: false,
			};
		});
		this.setCurrentScoreCategory(key);
		this.getSubCategoryScores(this.state.currentCategoryScore.pk, key, this.checkFormInputs());
		if (this.state.evaluation.is_human || this.state.evaluation.is_scan) this.getHumanIndicator(key, this.prepareFormInputs());
		else {
			this.getDiagIndicator(key, this.prepareFormInputs());
		}
	};

	handleVersion = (e) => {
		const selectedVersion = e.target.value;

		const slugify = (text) => {
			return text
				.toLowerCase()
				.normalize('NFD') // Normaliser les caractères
				.replace(/[\u0300-\u036f]/g, '') // Enlever les accents
				.replace(/[^a-z0-9 -]/g, ''); // Enlever les caractères non autorisés
		};

		const [year, month] = selectedVersion.split('-');
		const selectedVersionSlugified = `${year}-${slugify(month)}`;
		const newUrl = `/${this.state.entity.slug}/${this.state.product.slug}/assess/${selectedVersionSlugified}`;

		window.location.href = newUrl;
	};

	checkFormInputs() {
		let result = false;
		// Default Human Filters
		Object.entries(this.state.defaultFormInputs).forEach(([key, value]) => {
			result ||= value.length > 0;
		});
		// Human Criteria Filters
		Object.entries(this.state.humanCriteriaFormInputs).forEach(([key, value]) => {
			result ||= value.length > 0;
		});
		return result;
	}

	prepareFormInputs() {
		let inputs = { default: {}, human_criteria: [] };
		// Default Human Filters
		Object.entries(this.state.defaultFormInputs).forEach(([key, value]) => {
			inputs['default'][key] = [];
			inputs['default'][key].push(...value);
		});
		// Human Criteria Filters
		Object.entries(this.state.humanCriteriaFormInputs).forEach(([key, value]) => {
			inputs['human_criteria'].push(...value);
		});
		this.setState({ pdfactualfilter: JSON.stringify(inputs) });

		return inputs;
	}

	redirectFormTab(key, isChild) {
		if (isChild)
			this.setState({
				activeChildFormTab: key,
				showChildForm: true,
				activeMainFormTab: '',
			});
		else
			this.setState({
				activeMainFormTab: key,
				showChildForm: false,
				activeChildFormTab: '',
			});
	}

	// --------------------- generate html element from js -------------------------
	globalScoresDescItem(color, value, isEntity = false) {
		return (
			<div className="d-inline-flex align-items-center mb-3">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? <strong>{value}</strong> : <span>{value}</span>}
			</div>
		);
	}

	createListFromKeys(keysList) {
		let result = {};
		keysList.forEach((key) => (result[key] = []));
		return result;
	}

	customizedTabTitle(slug, value) {
		return (
			<div>
				<span className={`bullet bullet-${slug}`}></span>
				<span className="mxt--small-bold">{gettext(value)}</span>
			</div>
		);
	}

	setShowForm(boolean) {
		this.setState({ showForm: boolean });
	}

	setShowChildForm(boolean) {
		this.setState({ showChildForm: boolean });
	}

	clearFormFilters(e) {
		let defaultKeys = Object.keys(this.state.defaultFormInputs);
		let humanCriteriaKeys = Object.keys(this.state.humanCriteriaFormInputs);
		this.setState(
			{
				defaultFormInputs: this.createListFromKeys(defaultKeys),
				humanCriteriaFormInputs: this.createListFromKeys(humanCriteriaKeys),
			},
			() => {
				this.submitHumanForm(e);
			},
		);
	}

	activeFiltersName() {
		var results = [];

		if (this.state.defaultFormInputs) {
			Object.entries(this.state.defaultFormInputs).map(([key, values]) => {
				values.map((id) => {
					results.push(
						<h4
							key={this.state.defaultFormChoices[key].choices[id]}
							className="border py-1 px-3 mb-3 me-2"
							style={{
								borderRadius: '4px',
								backgroundColor: '#FAFAFA',
								borderColor: '#F0F0F0',
								width: 'fit-content',
								fontSize: '15px',
								fontWeight: '500',
								letterSpacing: '-0.02rem',
							}}
						>
							{this.state.defaultFormChoices[key].choices[id]}
						</h4>,
					);
				});
			});
		}
		if (this.state.humanCriteriaFormInputs) {
			Object.entries(this.state.humanCriteriaFormInputs).map(([key, values]) => {
				values.map((id) => {
					results.push(
						<h4
							key={this.state.humanCriteriaFormChoices[key].choices[id]}
							className="border py-1 px-3 mb-3 me-2"
							style={{
								borderRadius: '4px',
								backgroundColor: '#FAFAFA',
								borderColor: '#F0F0F0',
								width: 'fit-content',
								fontSize: '15px',
								fontWeight: '500',
								letterSpacing: '-0.02rem',
							}}
						>
							{this.state.humanCriteriaFormChoices[key].choices[id]}
						</h4>,
					);
				});
			});
		}
		if (results.length !== 0)
			return (
				<div className="d-flex flex-wrap">
					{results.map((result) => {
						return result;
					})}
				</div>
			);
	}

	submitHumanForm = async (event) => {
		event.preventDefault();
		await this.setState(() => {
			return {
				currentCategoryScoreLoaded: false,
				currentSubcategoryScoreLoaded: false,
				scoreCategoriesLoaded: false,
				currentSubcategoryScore: {},
				Indicatorsloaded: false,
				Indicators: {},
				nbCollaboratorsLoaded: false,
				nbWorkforceLoaded: false,
				nbAnswersLoaded: false,
				scoreCategories: undefined,
				HumanCollaboratorInfoLoaded: false,
				appliedForm: false,
				showForm: false,
				currentCategorySlug: 'all',
			};
		});
		let bodycontent = JSON.stringify(this.prepareFormInputs());
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json;charset=utf-8',
				'X-CSRFToken': csrftoken,
			},
			body: bodycontent,
		};
		this.getCollaboratorsCounts(requestOptions);
		this.updatescorecategoryfiltered(requestOptions);
		this.getSubCategoryScores(this.state.currentCategoryScore.pk, this.state.currentCategorySlug, this.checkFormInputs());
		if (this.state.isHumanPage || this.state.isScanPage) {
			this.getHumanIndicator(this.state.currentCategorySlug, this.prepareFormInputs());
			this.getHumanCollaboratorInfo(bodycontent);
			this.getHumanRadarData(bodycontent);
		} else if (this.state.isDiagPage) {
			this.getDiagCaracteristics();
		}
	};

	handleHumanFormTab(tabKey, inputKey, isDefault) {
		let inputsList = isDefault ? this.state.defaultFormInputs : this.state.humanCriteriaFormInputs;
		if (inputsList[tabKey].length != 0) {
			if (inputsList[tabKey].includes(inputKey)) inputsList[tabKey] = inputsList[tabKey].filter((choiceKey) => choiceKey !== inputKey);
			else inputsList[tabKey].push(inputKey);
		} else {
			inputsList[tabKey].push(inputKey);
		}
		if (isDefault) this.setState({ defaultFormInputs: inputsList });
		else this.setState({ humanCriteriaFormInputs: inputsList });
	}

	collaboratorsCountItem(title, count) {
		return (
			<div className="d-flex flex-column my-3">
				<div className="assess_human_collab_count_title">{title}</div>
				<div className="assess_human_collab_count_number">{count}</div>
			</div>
		);
	}

	humanFormTab(formChoices, tabTitle, tabEventKey, isDefault) {
		if (formChoices) {
			let checkedConditionList = isDefault ? this.state.defaultFormInputs[tabEventKey] : this.state.humanCriteriaFormInputs[tabEventKey];
			return (
				<Tab ket={tabEventKey} eventKey={`human_${tabEventKey}_form`} title={tabTitle}>
					{Object.entries(formChoices).map(([key, value]) => {
						return (
							<Form.Check
								type="checkbox"
								id={`${key}`}
								checked={checkedConditionList.includes(key) ? true : false}
								label={value}
								key={key}
								className={`d-flex align-items-center ${isDefault ? 'collab_filter' : 'collab_human_criteria'}`}
								onChange={
									isDefault ? () => this.handleHumanFormTab(tabEventKey, key, true) : () => this.handleHumanFormTab(tabEventKey, key, false)
								}
							/>
						);
					})}
				</Tab>
			);
		}
	}

	formButtons(isChild, outsideModals) {
		let choicesList = {};
		if (outsideModals) {
			choicesList = this.state.defaultFormChoices;
		} else {
			choicesList = isChild ? this.state.humanCriteriaFormChoices : this.state.defaultFormChoices;
		}
		return (
			<div className={outsideModals ? 'd-flex row-flex' : 'd-flex row-flex button-container'}>
				{Object.entries(choicesList).map(([key, value]) => {
					return (
						<button
							key={key}
							className="button border py-2 px-4 me-2 align-middle button--circle button--primary"
							style={{
								fontWeight: '550',
								display: 'inline-flex',
								backgroundColor:
									!outsideModals &&
									((!isChild && this.state.activeMainFormTab.includes(key)) || (isChild && this.state.activeChildFormTab.includes(key)))
										? '#534B8B'
										: '#423c6b',
							}}
							onClick={() => {
								if ((!isChild && this.state.activeMainFormTab.includes(key)) || (isChild && this.state.activeChildFormTab.includes(key))) {
									if (!isChild) {
										this.setState({
											activeMainFormTab: '',
										});
									}
									if (isChild && outsideModals) {
										this.setState({ showChildForm: true });
									}
									if (isChild && !outsideModals) {
										this.setState({
											activeChildFormTab: '',
										});
									}
								} else {
									if (outsideModals) {
										this.setShowForm(true);
									}
									this.redirectFormTab(`human_${key}_form`, isChild);
								}
							}}
						>
							{gettext(value['title'])}
							{!outsideModals && (
								<>
									<svg
										style={{
											height: '10px',
											width: '16px',
											marginLeft: '7px',
										}}
										className={
											(!isChild && this.state.activeMainFormTab.includes(key)) || (isChild && this.state.activeChildFormTab.includes(key))
												? 'arrow-down'
												: 'arrow-up'
										}
									>
										<path
											fill-rule="evenodd"
											clip-rule="evenodd"
											d="M0.205024 0.705014C0.478396 0.431662 0.921611 0.431662 1.19498 0.705014L6.30003 5.81007L11.4051 0.705014C11.6784 0.431662 12.1217 0.431662 12.395 0.705014C12.6684 0.978365 12.6684 1.42161 12.395 1.69496L6.795 7.29499C6.52165 7.56834 6.07841 7.56834 5.80506 7.29499L0.205024 1.69496C-0.0683414 1.42161 -0.0683414 0.978365 0.205024 0.705014Z"
											fill="white"
										/>
									</svg>
								</>
							)}
						</button>
					);
				})}
				{(outsideModals || !isChild) && (
					<button
						className="button border py-2 px-4 me-2 align-middle button--circle button--primary"
						style={{
							fontWeight: '550',
							backgroundColor: this.state.showChildForm ? 'rgb(83, 75, 139)' : 'rgb(66, 60, 107)',
						}}
						onClick={() => {
							if (this.state.showChildForm) {
								this.setShowChildForm(false);
							} else {
								this.setShowChildForm(true);
							}
							if (this.state.showForm && !this.state.showChildForm) {
								this.setShowChildForm(true);
							}
							this.setShowForm(true);
							this.setState({
								activeChildFormTab: this.state.defaultChilfFormTab,
								activeMainFormTab: '',
							});
						}}
					>
						{gettext('Autres')}
					</button>
				)}
				{outsideModals && (
					<button className="button align-middle" style={{ border: 'none' }} onClick={(e) => this.clearFormFilters(e)}>
						<i className="icon-trash"></i>
					</button>
				)}
			</div>
		);
	}

	updateState = (key, value) => {
		this.setState({ [key]: value });
	};

	render() {
		return !this.state.entityLoaded && !this.state.evaluationLoaded ? (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		) : (
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
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/' + this.state.entity.slug}>{gettext('Accueil')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mesurer')}</Breadcrumb.Item>
						<Breadcrumb.Item active>
							<strong>
								{this.state.product.slug === 'human'
									? gettext('Mixity Human')
									: this.state.product.slug === 'scan'
									? gettext('Mixity Scan')
									: gettext('Mixity Diag')}
							</strong>
						</Breadcrumb.Item>
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
				{/* Body */}
				<div className="col py-3 dashboard-assess-indicator-font-size">
					<div className="p-4 mt-4">
						<div className="row m-3 align-items-center justify-content-between">
							{/* Notification pour les demandes de réévaluation */}
							<NotificationLoader
								apiUrl={`${this.state.urlEvaluation}/api/${this.state.evaluation.pk}/reopening-request`}
								method="POST"
								is_active={`${this.state.notification_is_active}`}
								onRequestComplete={this.handleRequestComplete}
							/>

							{/* Liste d'évaluations */}
							{this.state.product && (
								<>
									<h3 className="mxt--large-bold col-6">
										{gettext('Mes Évaluations ')}
										{this.state.productLoaded && <span>{this.state.product.label}</span>}
									</h3>
									{/* Select et Tooltip */}
									<div className="col-3 d-flex justify-content-end">
										<select
											defaultValue={this.state.evaluation.display_version}
											onChange={(e) => this.handleVersion(e)}
											className="selector border d-flex me-5"
										>
											{this.state.versionsList.map((evaluation) => (
												<option key={evaluation.display_version} value={evaluation.display_version}>
													{evaluation.display_version}
												</option>
											))}
										</select>
									</div>
								</>
							)}
						</div>

						{/* Message for direct download */}
						<div id="direct_download_element" className="row m-3" style={{ display: 'none', borderRadius: '20px' }}>
							<h4 style={{ textAlign: 'center' }} id="direct_download_msg"></h4>
						</div>
						{/* Footprint and Downloads Block */}
						<div className="row m-3">
							<DisplayFootprint
								evaluation={this.state.evaluation}
								entity={this.state.entity}
								global_score_delta={this.state.global_score_delta}
								mean_score={this.state.mean_score}
								mean_score_in_business_line={this.state.mean_score_in_business_line}
								scoreCategoriesLoaded={this.state.scoreCategoriesLoaded}
								scoreCategories={this.state.scoreCategories}
								radarData={this.state.radarData}
							/>
							{/* Downloads Block */}
							<DisplayDownloads
								evaluation={this.state.evaluation}
								entity={this.state.entity}
								entityLoaded={this.state.entityLoaded}
								isDiagPage={this.state.isDiagPage}
								isScanPage={this.state.isScanPage}
								versionsList={this.state.versionsList}
								is_reader={this.state.is_reader}
								is_owner={this.state.is_owner}
								enabled_lang={this.state.enabled_lang}
								languages={this.state.languages}
								evaluationStarted={this.state.evaluationStarted}
								nbAnswers={this.state.nbAnswers}
								product={this.state.product}
								formChoicesLoaded={this.state.formChoicesLoaded}
								human_selected_filters={this.state.human_selected_filters}
								google_sheet_lang={this.state.google_sheet_lang}
								handleRequest={this.handleRequest}
								refresh_entity_evaluation={this.refresh_entity_evaluation}
								urlEvaluation={this.state.urlEvaluation}
								isSubscriptionCurrent={this.state.isSubscriptionCurrent}
								DiagCaracteristicsLoaded={this.state.DiagCaracteristicsLoaded}
								HumanCollaboratorInfoLoaded={this.state.HumanCollaboratorInfoLoaded}
								synthesis={this.state.synthesis}
							/>
						</div>
						{(this.state.evaluation.is_human || this.state.evaluation.is_scan) && (
							<div className="row m-3">
								<div className="d-flex justify-content-between align-items-center mb-4">
									<h3 className="mxt--large-bold mb-0" style={{ marginBottom: '1.5em' }}>
										{gettext('Caractéristiques des collaborateurs (f/h/nb)')}
									</h3>
									{/* Human Filters Form Block */}
									{this.state.Indicatorsloaded && (
										<div className="btn-group">
											{this.formButtons(false, true)}
											{/* Main Form */}
											<Modal
												show={this.state.showForm}
												onHide={() => this.setShowForm(false)}
												aria-labelledby="contained-modal-title-vcenter"
												size={'lg'}
												style={{ zIndex: '1050' }}
												className="criteria_modal m-0 p-0"
												centered
											>
												<Modal.Header closeButton className="align-items-start" style={{ border: 'none' }}>
													<div className="w-100">
														{this.formButtons(false, false)}
														{this.state.showChildForm && (
															<div
																className="w-100"
																style={{
																	overflow: 'hidden',
																	marginTop: '10px',
																}}
															>
																{this.formButtons(true, false)}
															</div>
														)}
													</div>
												</Modal.Header>
												<Modal.Body>
													{!this.state.showChildForm ? (
														<Tabs
															defaultActiveKey={this.state.activeMainFormTab}
															activeKey={this.state.activeMainFormTab}
															id="assess_human_main_form_tabs"
															style={{
																display: 'none',
															}}
														>
															{/*  Default form choices */}
															{Object.entries(this.state.defaultFormChoices).map(([key, value]) => {
																return this.humanFormTab(value['choices'], value['title'], key, true);
															})}
														</Tabs>
													) : (
														<Tabs
															// className="d-flex"
															defaultActiveKey={this.state.activeChildFormTab}
															activeKey={this.state.activeChildFormTab}
															id="assess_human_child_form_tabs"
															style={{
																display: 'none',
															}}
														>
															{/* Human criteria form choices */}
															{Object.entries(this.state.humanCriteriaFormChoices).map(([key, value]) => {
																return this.humanFormTab(value['choices'], value['title'], key, false);
															})}
														</Tabs>
													)}
												</Modal.Body>
												<Modal.Footer>
													{/* put element on the left side */}
													<div className="me-auto">
														<button
															className="button border align-middle button--circle button--primary"
															style={{
																fontWeight: '550',
															}}
															onClick={this.submitHumanForm}
														>
															{gettext('Appliquer les filtres')}
														</button>
														<button
															className="button align-middle"
															style={{
																border: 'none',
															}}
															onClick={(e) => this.clearFormFilters(e)}
														>
															<i className="icon-trash"></i>
														</button>
													</div>
												</Modal.Footer>
											</Modal>
										</div>
									)}
									{this.state.appliedForm && (
										<div>
											<h5>{gettext('Filtres actifs :')}</h5>
											{this.activeFiltersName()}
										</div>
									)}
								</div>
								<div className="d-flex flex-column w-100" style={{ gap: '2rem' }}>
									<div className="d-flex flex-row" style={{ gap: '2rem' }}>
										{/* Collaborators Counts Block */}
										<div className="col" style={{ maxWidth: '50%' }}>
											<Card className="d-flex flex-row align-items-center assess_human_collab_count">
												<div className="col">
													<div className="d-flex flex-column">
														{/* Collborators Count */}
														{this.state.nbWorkforceLoaded ? (
															this.collaboratorsCountItem(gettext('Effectif Total'), this.state.nbWorkforceTotal)
														) : (
															<Skeleton variant="text" width={52} />
														)}
														{this.state.evaluation.is_scan &&
															this.state.nbCollaboratorsLoaded &&
															this.collaboratorsCountItem(
																gettext('Nombres de collaborateurs sollicités'),
																this.state.nbCollaboratorsTotal,
															)}
														{this.state.nbCollaboratorsLoaded ? (
															this.collaboratorsCountItem(
																gettext('Total des réponses collectées'),
																this.state.evaluation.is_human ? this.state.nbCollaborators : this.state.nbAnswers,
															)
														) : (
															<Skeleton variant="text" width={52} />
														)}
														{this.state.nbWorkforceLoaded && this.state.nbCollaboratorsLoaded ? (
															this.collaboratorsCountItem(
																gettext('Ratio des réponses collectées'),
																`${Math.round(
																	(this.state.evaluation.is_human
																		? this.state.nbCollaborators / this.state.nbCollaboratorsTotal
																		: this.state.nbAnswers / this.state.nbCollaboratorsTotal) * 100,
																)}%`,
															)
														) : (
															<Skeleton variant="text" width={52} />
														)}
													</div>
												</div>
												<div className="col d-flex justify-content-end">
													<div style={{ width: '70%' }}>
														<img src={'/static/img/assess/human_collab_counts.png'} alt="Graphique des collaborateurs Human" />
													</div>
												</div>
											</Card>
										</div>
										{this.state.HumanCollaboratorInfoLoaded && this.state.CollaboratorsIndicators && (
											<React.Fragment>
												<div
													className="col"
													style={{
														maxWidth: '50%',
													}}
												>
													<div
														className="d-flex flex-row justify-content-between card"
														style={{
															borderRadius: '25px',
														}}
													>
														{this.state.CollaboratorsIndicators.slice(0, 2).map((indicator) => {
															indicator.display_params.linked_with.push(indicator.id);
															return (
																<AssessIndicators
																	key={indicator.title}
																	category={'all'}
																	json={indicator}
																	index={indicator.id}
																	isCriteria={true}
																/>
															);
														})}
													</div>
												</div>
											</React.Fragment>
										)}
									</div>
									<ShowMoreCharacteristics
										HumanCollaboratorInfoLoaded={this.state.HumanCollaboratorInfoLoaded}
										CollaboratorsIndicators={this.state.CollaboratorsIndicators}
										showCollaboratorsIndicators={this.state.showCollaboratorsIndicators}
										updateParentState={this.updateState}
									/>
								</div>
							</div>
						)}
						<DisplayEvaluationSynthesis
							evaluationId={this.state.evaluation.pk}
							storedScoreCategory={this.state.storedScoreCategory}
							DiagCaracteristicsLoaded={this.state.DiagCaracteristicsLoaded}
							HumanCollaboratorInfoLoaded={this.state.HumanCollaboratorInfoLoaded}
							synthesis={this.state.synthesis}
							updateParentState={this.updateState}
						/>
						{/* Assess Page Data Blocks : Global Scores, Indicators, Strength and Weaknesses Blocks */}
						{this.state.DiagCaracteristicsInfo && this.state.DiagCaracteristicsLoaded && (
							<React.Fragment>
								<div className="card p-3 m-2">
									<div
										className="d-flex justify-content-between align-items-middle"
										style={{ cursor: 'pointer' }}
										onClick={() =>
											this.setState({
												showCollaboratorsIndicators: !this.state.showCollaboratorsIndicators,
											})
										}
									>
										<h3 className="mxt--normal-bold mb-0 me-2">{gettext("Caractéristiques de l'entreprise")}</h3>
										<img
											style={{
												width: '2%',
												transition: 'transform 0.3s',
												transform: this.state.showCollaboratorsIndicators ? 'rotate(180deg)' : 'rotate(0deg)',
											}}
											src={'/static/icon/chevron-dropdown.svg'}
											alt="v"
										/>
									</div>
									{this.state.showCollaboratorsIndicators && (
										<React.Fragment>
											<Card className="d-flex flex-row align-items-center assess_human_collab_count my-4">
												<div className="col-10">
													<div className="d-flex justify-content-start flex-wrap">
														{this.state.DiagCaracteristicsInfo.slice(0, 5).map((data) => {
															return (
																<div className={'w-50'}>
																	{this.collaboratorsCountItem(data.label, data.subs_values ? data.subs_values : data.value)}
																</div>
															);
														})}
													</div>
												</div>
												<div className="col-2 d-flex justify-content-end">
													<div
														style={{
															width: '100%',
														}}
													>
														<img
															src={'/static/img/assess/human_collab_counts.png'}
															alt="Graphique des caractéristiques d'entreprise"
														/>
													</div>
												</div>
											</Card>
											<Card className="d-flex flex-row align-items-center assess_human_collab_count_2">
												<div className="col-10">
													<div className="d-flex justify-content-start flex-wrap">
														{this.state.DiagCaracteristicsInfo.slice(5, 10).map((data) => {
															return (
																<div className={'w-50'}>
																	{this.collaboratorsCountItem(data.label, data.subs_values ? data.subs_values : data.value)}
																</div>
															);
														})}
													</div>
												</div>
												<div className="col-2 d-flex justify-content-end">
													<div
														style={{
															width: '100%',
														}}
													>
														<img
															src={'/static/img/assess/diag_caracteristics.png'}
															alt="Graphique des caractéristiques d'entreprise"
														/>
													</div>
												</div>
											</Card>
											{/* Caractéristiques pour campus */}
											{this.state.evaluation.is_campus && (
												<Card className="d-flex flex-row align-items-center assess_human_collab_count_3 my-4">
													<div className="col-10">
														<div className="d-flex justify-content-start flex-wrap">
															{this.state.DiagCaracteristicsInfo.slice(10, 12).map((data) => {
																return (
																	<div className={'w-50'}>
																		{this.collaboratorsCountItem(
																			data.label,
																			data.subs_values ? data.subs_values : data.value,
																		)}
																	</div>
																);
															})}
														</div>
													</div>
													<div className="col-2 d-flex justify-content-end">
														<div
															style={{
																width: '100%',
															}}
														>
															<img
																src={'/static/img/assess/diag_caracteristics.png'}
																alt="Graphique des caractéristiques d'entreprise"
															/>
														</div>
													</div>
												</Card>
											)}
										</React.Fragment>
									)}
								</div>
							</React.Fragment>
						)}
						{this.state.evaluation.is_scan && this.state.evaluation.is_validated_by_admin && (
							<div className="row m-3 mb-4">
								<DisplayProfileRepartition data={this.state.evaluation.get_collaborators_profile_levels} />
							</div>
						)}
						{this.state.evaluation.get_computed_values_by_skills && this.state.evaluation.is_validated_by_admin && (
							<div className="row m-3 mb-4">
								<DisplayDataRepartitionBySkills
									datas={this.state.evaluation.get_computed_values_by_skills}
									updateParentState={this.updateState}
								/>
							</div>
						)}
						{this.state.evaluation.get_computed_values_by_subcategories && this.state.evaluation.is_validated_by_admin && (
							<div className="row m-3 mb-4">
								<DisplayScoringPerStages
									data={{ subcategories: this.state.evaluation.get_computed_values_by_subcategories, benchmark: true }}
								/>
							</div>
						)}
						{this.state.evaluation.is_validated_by_admin && this.state.scoreCategoriesLoaded && (
							<div className="row m-3">
								{!this.state.evaluation.is_scan && (
									<h3 className="mxt--large-bold" id="evaluation-tabs">
										{gettext('Mon évaluation')}
									</h3>
								)}
								<Tabs
									defaultActiveKey={this.state.defaultCategoryScore.category.slug}
									onSelect={this.handleActiveTab}
									id="assess-tabs"
									className="mb-3"
								>
									{this.state.tabsCategoriesLoaded &&
										this.state.tabsCategories.map((cat) => {
											return (
												<Tab
													tabClassName={`nav-color nav-color-${cat.slug}`}
													key={cat.pk}
													eventKey={cat.slug}
													title={this.customizedTabTitle(cat.slug, cat.name)}
												>
													{/* Global Scores Block */}
													{cat.slug != 'csrd' && (
														<Card
															style={{
																borderRadius: '25px',
															}}
														>
															<Card.Body className="assess_global_scores">
																{/* Rendering global scores in function of current score category */}
																{this.state.currentCategoryScoreLoaded && (
																	<div id={`assess_global_scores_desc_${cat.slug}`} className="assess_global_scores_desc">
																		<h3 className="mxt--large-bold">{gettext('Scores globaux')}</h3>
																		<div className="d-flex flex-column flex-start">
																			{this.globalScoresDescItem(cat.color, this.state.entity.name, true)}
																			{this.globalScoresDescItem(
																				getColors('meanscore_sector', [1]),
																				gettext('Score moyen dans mon secteur'),
																			)}
																			{this.globalScoresDescItem(
																				getColors('meanscore_global', [1]),
																				gettext('Score moyen dans toutes les entreprises'),
																			)}
																		</div>
																	</div>
																)}
																{this.state.currentCategoryScoreLoaded ? (
																	<div
																		id={`assess_global_scores_category_${cat.slug}`}
																		className="assess_global_scores_category"
																	>
																		<AssessCategoryScore
																			innerPercent={Math.round(this.state.currentCategoryScore.inner_percent)}
																			innerColor={cat.color}
																			betweenPercent={Math.round(this.state.currentCategoryScore.between_percent)}
																			outterPercent={Math.round(this.state.currentCategoryScore.outter_percent)}
																		/>
																	</div>
																) : (
																	<AssessCategoryScoreSkeletonLoader skeletonsCount={1} />
																)}
																{this.state.product.slug === 'scan' ? (
																	<div style={{ width: '40%', textAlign: 'end' }} className="m-3">
																		<div className={`w-100 scan-dimension-content-color-${cat.slug}`}>
																			<h3 className="mxt--normal-bold">{gettext(cat.name)}</h3>
																		</div>
																		<div className="d-flex flex-column">
																			<p className="mxt--small p-0 m-0 mt-3">
																				{this.state.dimensions_infos[cat.slug][0]}
																			</p>
																			<p className="mxt--small p-0 m-0 mt-2">
																				{this.state.dimensions_infos[cat.slug][1]}
																			</p>
																		</div>
																	</div>
																) : this.state.currentCategoryScoreLoaded &&
																  this.state.currentSubcategoryScoreLoaded &&
																  this.state.currentSubcategoryScore[cat.slug] ? (
																	<div id="assess_global_scores_subcategories" className="assess_global_scores_subcategories">
																		{this.state.currentSubcategoryScore[cat.slug].map((score_subcat) => {
																			return (
																				<AssessSubCategoryScore
																					key={score_subcat[0]}
																					subCatPercent={Math.round(score_subcat[1])}
																					subCatName={score_subcat[0]}
																					subCatColor={cat.color}
																					benchmarkActive={false}
																				/>
																			);
																		})}
																	</div>
																) : (
																	<AssessSubCategoryScoreSkeletonLoader skeletonsCount={5} />
																)}
															</Card.Body>
														</Card>
													)}
													{this.state.evaluation.is_validated_by_user &&
														this.state.evaluation.is_validated_by_admin &&
														this.state.scoreCategoriesLoaded && (
															<div className="row my-3">
																<StrengthsAndWeaknesses
																	strengths={this.state.evaluation.strengths.filter(
																		(strength) => strength.category === this.state.currentCategorySlug,
																	)}
																	weaknesses={this.state.evaluation.weaknesses.filter(
																		(weakness) => weakness.category === this.state.currentCategorySlug,
																	)}
																	aims={this.state.evaluation.aims.filter(
																		(aim) => aim.category === this.state.currentCategorySlug,
																	)}
																	CommentsLoaded={this.state.CommentsLoaded}
																/>
															</div>
														)}
													{(this.state.evaluation.is_human || this.state.evaluation.is_scan) &&
													this.state.nbCollaborators <= this.state.nbCollaboratorsWithFilterMin ? (
														<div
															style={{
																textAlign: '-webkit-center',
																margin: '50px 0',
															}}
														>
															<div className="item_pb item_s50 item_c stretched_item">
																<h3
																	className="txt_line content-strong"
																	style={{
																		margin: 'auto',
																	}}
																>
																	{gettext(
																		"Le nombre de répondants (f/h/nb) dans cette catégorie n'est pas assez important pour visualiser les résultats",
																	)}
																</h3>
															</div>
														</div>
													) : (
														// Indicators Block
														this.state.Indicatorsloaded && (
															<>
																{this.state.showIndicators && this.state.Indicatorsloaded && (
																	<div className="d-flex flex-row flex-wrap mt-3">
																		{this.state.currentCategorySlug == 'cultural_diversity' &&
																			this.state.namsorIndicatorContent &&
																			this.state.namsorIndicatorContent.length > 0 && (
																				<div
																					key={'namsorIndicator'}
																					className="d-flex flex-row flex-wrap justify-content-between card"
																					style={{
																						margin: '1rem',
																						borderRadius: '25px',
																						width: '97%',
																					}}
																				>
																					<NamsorIndicator results={this.state.namsorIndicatorContent} />
																				</div>
																			)}
																		{this.state.Indicators[this.state.currentCategorySlug] &&
																			this.state.linkedWithList.map((linked, index) => {
																				if (
																					this.state.Indicators[this.state.currentCategorySlug].find(
																						(element) => element.scores_json.id === linked[0],
																					) &&
																					linked.length > 1
																				)
																					return (
																						<div
																							key={index}
																							className="d-flex flex-row flex-wrap justify-content-between card"
																							style={{
																								margin: '1rem',
																								borderRadius: '25px',
																								width: '97.5%',
																							}}
																						>
																							{this.state.Indicators[this.state.currentCategorySlug]
																								.filter((element) => linked.includes(element.scores_json.id))
																								.map((element, index) => {
																									return (
																										<AssessIndicators
																											key={element.title}
																											category={this.state.currentCategorySlug}
																											json={element.scores_json}
																											index={index}
																											isCriteria={false}
																											svg={
																												element.scores_json.indicator_type ===
																													'TextChart' && index === linked.length - 1
																													? this.state.Indicators[
																															this.state.currentCategorySlug
																													  ].find(
																															(element) =>
																																linked[0] ===
																																element.scores_json.id,
																													  ).scores_json.display_params.svg
																													: ''
																											}
																											isHuman={!this.state.isDiagPage}
																										/>
																									);
																								})}
																						</div>
																					);
																				else {
																					{
																						var indicator = this.state.Indicators[
																							this.state.currentCategorySlug
																						].find((element) => linked[0] === element.scores_json.id);
																						if (
																							indicator &&
																							indicator.scores_json.indicator_type === 'MultipleBarChart'
																						)
																							return (
																								<div
																									key={indicator.title}
																									className="d-flex flex-row justify-content-between card"
																									style={{
																										margin: '1rem',
																										borderRadius: '25px',
																										width: '97%',
																									}}
																								>
																									<AssessIndicators
																										category={this.state.currentCategorySlug}
																										json={indicator.scores_json}
																										index={0}
																										isCriteria={false}
																										isHuman={!this.state.isDiagPage}
																									/>
																								</div>
																							);
																						else if (indicator)
																							return (
																								<AssessIndicators
																									key={indicator.title}
																									category={this.state.currentCategorySlug}
																									json={indicator.scores_json}
																									index={0}
																									isCriteria={false}
																									isHuman={!this.state.isDiagPage}
																								/>
																							);
																					}
																				}
																			})}
																	</div>
																)}
																<div className="card p-1 my-3">
																	<div
																		className="d-flex justify-content-center align-items-center p-3"
																		style={{ cursor: 'pointer' }}
																		onClick={() => {
																			this.setState({
																				showIndicators: !this.state.showIndicators,
																			});
																		}}
																	>
																		{this.state.showIndicators ? (
																			<h3 className="mxt--normal m-0">{gettext('Cacher résultats détaillés')}</h3>
																		) : (
																			<h3 className="mxt--normal m-0">{gettext('Voir les résultats détaillés')}</h3>
																		)}
																	</div>
																</div>
															</>
														)
													)}
												</Tab>
											);
										})}
								</Tabs>
							</div>
						)}
					</div>
				</div>
			</div>
		);
	}
}

export default AssessPage;

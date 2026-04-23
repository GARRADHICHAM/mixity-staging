import React, { useState } from 'react';

export function QuestionTypeGeneratorComponent(props) {
	function emptyRule() {
		return { mandatory_tags: [], forbidden_tags: [], rule: null };
	}

	const [type, setType] = useState('');
	const [additionalType, setAdditionalType] = useState('');
	const [computeMethod, setComputeMethod] = useState('');
	const [compareBase, setCompareBase] = useState('');
	const [question, setQuestion] = useState('');
	const [questions, setQuestions] = useState('');
	const [countryData, setCountryData] = useState('');
	const [range, setRange] = useState('');
	const [mode, setMode] = useState('');
	const [importedType, setImportedType] = useState('');
	const [attributionMode, setAttributionMode] = useState('');
	const [isUnknown, setIsUnknown] = useState(false);
	const [rules, setRules] = useState([emptyRule()]);
	const [selectedRule, setSelectedRule] = useState(0);

	const availableTypes = {
		valeur: 'Valeur numérique. Peut être un entier, un décimal, négatif.',
		date: "Permet de demander une date en input. Pas de notation à l'heure actuelle.",
		qcm: "Question avec plusieurs choix que l'utilisateur sélectionne directement.",
		pourcentage: 'Valeur numérique. Peut être un entier, un décimal. Ne peut être négatif sans le type additionnel croissance.',
		subquestions: 'Type indiquant que la question possède différentes sous questions numériques.',
		subquestions_qcm: 'Type de sous-questions permettant de cocher plusieurs cases à un QCM. Contrairement au type QCM, les choix sont des sous-questions.',
		subquestions_dual: 'Type Human avec deux colonnes.',
	};
	const availableAdditionalTypes = {
		currency: 'Permet de rajouter la mention de la monnaie dans le questionnaire.',
		croissance: 'Autorise les valeurs négatives pour les pourcentages.',
	};
	const availableComputeMethod = {
		Standard: 'Les calculs sont directement effectués par rapport à la valeur de réponse.',
		ratio: 'On compare la valeur de réponse à une autre base (données de pays, autre question, ...) en faisant un ratio réponse/valeur comparée.',
		relative: 'On compare la valeur de réponse à une autre base (données de pays, autre question, ...) en faisant différence entre les deux.',
		json: 'Type avancé. Plus de détails sont présents dans les options en dessous.',
	};
	const availableCompareBase = {
		question: 'Permet de comparer la valeur à une question du référentiel',
		country: 'Permet de comparer la valeur à une donnée de pays',
	};
	const availableModes = {
		'ratio-questions':
			'Compare la valeur de réponse à la somme des questions en comparaison en faisant un ratio de ' +
			'la valeur de la réponse (ou la somme des valeurs des sous-questions) par rapport à la somme des ' +
			'réponses aux question en comparaison.',
		'subquestions-qcm-count': 'Permet de compter le nombre de cases cochées',
	};
	const availableAttributionModes = {
		range:
			'La valeur obtenue avec le mode choisi va être comparée à chaque valeur du range une à une. ' +
			'La première valeur du range qui est supérieure (strict) à la valeur obtenue précédemment définiera le choix. ' +
			'Le choix correspond à la position de la valeur du range dans la liste.',
	};

	function addRule() {
		setRules([...rules, emptyRule()]);
		setSelectedRule(selectedRule + 1);
	}

	/*
    Some types cannot be customized and can't do much other than storing the input of the user (no rating, ...)
     */
	function isStrictType(type) {
		return ['date', 'subquestions_dual'].includes(type);
	}

	function deleteRule() {
		rules.splice(selectedRule, 1);
		setRules([...rules]);
		if (selectedRule === rules.length) {
			setSelectedRule(selectedRule - 1);
		}
	}

	function moveUp() {
		const previous = rules[selectedRule - 1];
		rules[selectedRule - 1] = rules[selectedRule];
		rules[selectedRule] = previous;
		setSelectedRule(selectedRule - 1);
	}

	function moveDown() {
		const next = rules[selectedRule + 1];
		rules[selectedRule + 1] = rules[selectedRule];
		rules[selectedRule] = next;
		setSelectedRule(selectedRule + 1);
	}

	/*
        Function to generate the final JSON
     */
	function generateJson(unknownObj) {
		let json = { mode: mode };
		// For json types that only have 1 rule and no tag constraints, we generate directly set the rule at the root of JSON
		if (rules.length === 1 && rules[0].mandatory_tags.length === 0 && rules[0].forbidden_tags.length === 0) {
			json['attributionmode'] = attributionMode;
			if (attributionMode === 'range') {
				json['range'] = (rules[0].rule || '') !== '' ? rules[0].rule.split(' ').map(Number) : [];
			}
		} else {
			json['attributionmode'] = {
				type: 'tag-rule',
				attributionmode: attributionMode,
				rules: JSON.parse(JSON.stringify(rules)).map((rule) => {
					if (attributionMode === 'range') {
						rule['rule'] = (rule.rule || '') !== '' ? rule.rule.split(' ').map(Number) : [];
					}
					return rule;
				}),
			};
		}
		if (mode === 'ratio-questions') {
			json['questions'] = questions !== '' ? questions.split(' ') : [];
		}
		if (attributionMode === '' || mode === '') {
			unknownObj.flag = true;
		}
		return '_' + JSON.stringify(json);
	}

	function generateResult() {
		let variable = type;
		const unknownObj = {
			flag: true,
			valueOf() {
				return this.flag;
			},
		};

		unknownObj.flag = type === '';
		if (!isStrictType(type)) {
			variable += additionalType;
			if (additionalType.length > 0 && type.includes('_')) {
				unknownObj.flag = true;
			}
			if (computeMethod.length > 0) {
				variable += `_${computeMethod}`;
				if (computeMethod !== 'json') {
					if (compareBase === 'question') {
						variable += `_${question}`;
						if (question === '') {
							unknownObj.flag = true;
						}
					} else if (compareBase === 'country') {
						variable += `_country`;
						if (countryData.length > 0) {
							variable += `_${countryData}`;
						} else {
							unknownObj.flag = true;
						}
					} else {
						unknownObj.flag = true;
					}
				} else {
					variable += generateJson(unknownObj);
				}
			}
		}
		if (range.length > 0 && computeMethod !== 'json') {
			variable += `_${range.split(' ').join('_')}`;
		}
		if (isUnknown !== unknownObj.flag) setIsUnknown(unknownObj.flag);
		return variable;
	}

	function importJson(importedTypeSplited) {
		const importedJson = JSON.parse(importedTypeSplited.join('_'));
		setMode(importedJson['mode']);
		if (importedJson['mode'] === 'ratio-questions') {
			setQuestions(importedJson['questions'].join(' '));
		}
		if (importedJson['attributionmode'].constructor === {}.constructor) {
			setAttributionMode(importedJson['attributionmode']['attributionmode']);
			if (importedJson['attributionmode']['attributionmode'] === 'range') {
				importedJson['attributionmode']['rules'].forEach((rule) => {
					rule['rule'] = rule['rule'].join(' ');
				});
			}
			setRules(importedJson['attributionmode']['rules']);
		} else {
			setRules([emptyRule()]);
			if (importedJson['attributionmode'] === 'range') {
				rules[0].rule = importedJson['range'].join(' ');
			}
			setRules([...rules]);
			setAttributionMode(importedJson['attributionmode']);
		}
	}

	/*
    Function to import a type and prefill all the information in the form
     */
	function importType() {
		let importedTypeSplited = importedType.split('_');
		setComputeMethod('');
		setCompareBase('');
		setAdditionalType('');
		if (importedTypeSplited[0].endsWith('currency')) {
			setAdditionalType('currency');
			setType(importedTypeSplited[0].replace('currency', ''));
		} else if (importedTypeSplited[0].endsWith('croissance')) {
			setAdditionalType('croissance');
			setType(importedTypeSplited[0].replace('croissance', ''));
		} else {
			setType(importedTypeSplited[0]);
		}
		if (importedTypeSplited.length > 1) {
			if (importedTypeSplited[1] === 'dual' || importedTypeSplited[1] === 'qcm') {
				setType(type + '_' + importedTypeSplited[1]);
			} else {
				if (['ratio', 'relative', 'json'].includes(importedTypeSplited[1])) {
					setComputeMethod(importedTypeSplited[1]);
				}
			}

			if (importedTypeSplited[1] === 'json') {
				importedTypeSplited.splice(0, 2);
				importJson(importedTypeSplited);
				return;
			}
		}
		if (importedTypeSplited.length > 2) {
			if (importedTypeSplited[2] === 'json') {
				// only for subquestions_qcm
				importedTypeSplited.splice(0, 3);
				importJson(importedTypeSplited);
				return;
			}
			if (importedTypeSplited[1] === 'ratio' || importedTypeSplited[1] === 'relative') {
				setCompareBase(importedTypeSplited[2] === 'country' ? 'country' : 'question');
				if (importedTypeSplited.length > 3 && importedTypeSplited[2] === 'country') {
					setCountryData(importedTypeSplited[3]);
					importedTypeSplited.splice(3, 1);
				} else {
					setQuestion(importedTypeSplited[2]);
				}
				importedTypeSplited.splice(0, 3);
				setRange(importedTypeSplited.join(' '));
				return;
			}
		}

		if (importedTypeSplited.length > 1) {
			importedTypeSplited.splice(0, 1);
			setRange(importedTypeSplited.join(' '));
		}
	}

	return (
		<section className="container--nopadding">
			<h1>
				Générateur de type{' '}
				<button type="button" className="btn button--primary" data-bs-toggle="modal" data-bs-target="#importModal">
					<i className="fa fa-upload"></i> Importer un type
				</button>
			</h1>
			<div className="modal fade" id="importModal" tabIndex="-1" aria-labelledby="importModalLabel" aria-hidden="true" style={{ zIndex: 1000000 }}>
				<div className="modal-dialog">
					<div className="modal-content">
						<div className="modal-header">
							<h1 className="modal-title fs-5" id="importModalLabel">
								Importer un type
							</h1>
							<button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
						</div>
						<div className="modal-body">
							<textarea
								className="w-100"
								rows="4"
								value={importedType}
								onChange={(e) => {
									setImportedType(e.target.value);
								}}
							></textarea>
						</div>
						<div className="modal-footer">
							<button type="button" className="btn btn-primary" data-bs-dismiss="modal" onClick={importType}>
								Importer
							</button>
						</div>
					</div>
				</div>
			</div>

			<p>Le générateur de type permet de formatter un ensemble de règles pour les questions des référentiels qu'elles soient simples ou complexes.</p>
			<div className="row">
				<div className="col-lg-6 col-12">
					<label htmlFor="type">Type primitif : </label>
					<input
						placeholder="Ex: valeur"
						list="types"
						id="type"
						name="type"
						value={type}
						onChange={(e) => {
							setType(e.target.value);
						}}
					/>
					<datalist id="types">
						{Object.keys(availableTypes).map((key) => {
							return <option value={key}>{key}</option>;
						})}
					</datalist>
					<p>
						<strong>Description du type :</strong> <span id="type-description">{availableTypes[type] || 'Pas de description'}</span>
					</p>
					<div style={{ display: !isStrictType(type) ? '' : 'none' }}>
						<label htmlFor="additional-type">Type additionnel (optionnel) : </label>
						<input
							placeholder="Ex: croissance"
							list="additional-types"
							id="additional-type"
							name="additional-type"
							value={additionalType}
							onChange={(e) => {
								setAdditionalType(e.target.value);
							}}
						/>
						<datalist id="additional-types">
							{Object.keys(availableAdditionalTypes).map((key) => {
								return <option value={key}>{key}</option>;
							})}
						</datalist>
						<p>
							<strong>Description du type :</strong>{' '}
							<span id="additional-type-description">{availableAdditionalTypes[additionalType] || 'Pas de description'}</span>
						</p>
						<label htmlFor="compute-method">Méthode de calcul : </label>
						<select
							name="compute-method"
							id="compute-method"
							value={computeMethod}
							onChange={(e) => {
								setComputeMethod(e.target.value);
							}}
						>
							{Object.keys(availableComputeMethod).map((key) => {
								return <option value={key === 'Standard' ? '' : key}>{key}</option>;
							})}
						</select>
						<p>
							<strong>Description :</strong>{' '}
							<span id="compute-method-description">{availableComputeMethod[computeMethod] || 'Pas de description'}</span>
						</p>
						<div style={{ display: computeMethod !== 'json' ? '' : 'none' }}>
							<div id="compare-base-container" style={{ display: computeMethod === 'relative' || computeMethod === 'ratio' ? '' : 'none' }}>
								<label htmlFor="compare-base">Base de comparaison : </label>
								<select
									name="compare-base"
									id="compare-base"
									value={compareBase}
									onChange={(e) => {
										setCompareBase(e.target.value);
									}}
								>
									<option value="">-------</option>
									{Object.keys(availableCompareBase).map((key) => {
										return <option value={key}>{key}</option>;
									})}
								</select>
								<p>
									<strong>Description :</strong>{' '}
									<span id="compare-base-description">{availableCompareBase[compareBase] || 'Pas de description'}</span>
								</p>
							</div>
							<div id="question-number-container" style={{ display: compareBase === 'question' ? '' : 'none' }}>
								<label htmlFor="question-number">Numéro de question : </label>
								<input
									placeholder="Ex: 20214002"
									type="text"
									name="question-number"
									id="question-number"
									value={question}
									onChange={(e) => {
										setQuestion(e.target.value);
									}}
								/>
							</div>
							<div id="country-data-container" style={{ display: compareBase === 'country' ? '' : 'none' }}>
								<label htmlFor="country-data">Valeur de country data : </label>
								<input
									placeholder="Ex: paygapshift"
									list="country-data-types"
									id="country-data"
									name="country-data"
									value={countryData}
									onChange={(e) => {
										setCountryData(e.target.value);
									}}
								/>
								<datalist id="country-data-types">
									<option value="paygapshift">paygapshift</option>
									<option value="disabilityrate">disabilityrate</option>
									<option value="paygapmanagers">paygapmanagers</option>
									<option value="paygapoperatives">paygapoperatives</option>
									<option value="scholarshipstudent">scholarshipstudent</option>
								</datalist>
								<p>
									<strong>Description :</strong> <span id="country-data-description">Valeur de comparaison dans le Country Data (Admin)</span>
								</p>
							</div>
							<div>
								<label htmlFor="range">Intervalles de choix : </label>
								<input
									type="text"
									id="range"
									name="range"
									placeholder="Ex: 10 20 30 40"
									value={range}
									onChange={(e) => {
										setRange(e.target.value);
									}}
								/>
								<p>
									<strong>Description :</strong>{' '}
									<span id="range-description">
										Selon la valeur obtenue par la réponse (brute ou calculée selon les critères), on attribue des choix. Séparez vos
										intervalles avec des espaces. Ex: <strong>10 20 30 40</strong>. Si la valeur de réponse est inférieure à 10, le choix 1
										sera choisi. Si inférieure à 20, ce sera le choix 2, ... Les valeurs doivent être croissantes. Elles peuvent être
										négatives.
									</span>
								</p>
							</div>
						</div>
						<div style={{ display: computeMethod === 'json' ? '' : 'none' }}>
							<div id="mode-container">
								<label htmlFor="mode">Mode : </label>
								<select
									name="mode"
									id="mode"
									value={mode}
									onChange={(e) => {
										setMode(e.target.value);
									}}
								>
									<option value="">-----------</option>
									{Object.keys(availableModes).map((key) => {
										return <option value={key}>{key}</option>;
									})}
								</select>
								<p>
									<strong>Description :</strong> <span id="mode-description">{availableModes[mode] || 'Pas de description'}</span>
								</p>
							</div>
							<div id="attributionmode-container">
								<label htmlFor="attributionmode">Mode d'attribution : </label>
								<select
									name="attributionmode"
									id="attributionmode"
									value={attributionMode}
									onChange={(e) => {
										setAttributionMode(e.target.value);
									}}
								>
									<option value="">-----------</option>
									{Object.keys(availableAttributionModes).map((key) => {
										return <option value={key}>{key}</option>;
									})}
								</select>
								<p>
									<strong>Description :</strong>{' '}
									<span id="attributionmode-description">{availableAttributionModes[attributionMode] || 'Pas de description'}</span>
								</p>
							</div>

							<div style={{ display: mode === 'ratio-questions' ? '' : 'none' }}>
								<label htmlFor="questions">Questions : </label>
								<input
									type="text"
									id="questions"
									name="questions"
									placeholder="Ex: 20214001 20214002_0 20214002_1"
									value={questions}
									onChange={(e) => {
										setQuestions(e.target.value);
									}}
								/>
								<p>
									<strong>Description :</strong>{' '}
									<span id="questions-description">
										Ce sont les numéros de questions du Google Sheets qui permettront de faire un ratio de la valeur de la réponse par
										rapport à la somme de celles-ci. Les sous-questions peuvent aussi être indiquées en ajoutant
										<pre className="d-inline">
											_<i>N° de la sous question</i>
										</pre>
										. Ex: <i>2021004_0</i> (pour la première sous question de la question 2021004)
									</span>
								</p>
							</div>
							<div className="row mb-2 mr-0 gap-2" style={{ marginLeft: '0' }}>
								<select
									className="col-4"
									value={selectedRule}
									onChange={(e) => {
										setSelectedRule(parseInt(e.target.value));
									}}
								>
									{rules.map((rule, i) => {
										return <option value={i}>Règle {i + 1}</option>;
									})}
								</select>
								<button onClick={addRule} title="Ajouter" className="col-1 btn-success btn">
									<i className="fa fa-plus" />
								</button>
								{rules.length > 1 ? (
									<button onClick={deleteRule} title="Supprimer" className="col-1 btn-danger btn">
										<i className="fa fa-trash" />
									</button>
								) : (
									''
								)}
								{selectedRule > 0 ? (
									<button onClick={moveUp} title="Remonter" className="col-1 button--primary btn">
										<i className="fa fa-arrow-up" />
									</button>
								) : (
									''
								)}
								{selectedRule < rules.length - 1 ? (
									<button onClick={moveDown} title="Descendre" className="col-1 button--primary btn">
										<i className="fa fa-arrow-down" />
									</button>
								) : (
									''
								)}
							</div>
							{rules
								.filter((rule, i) => i === selectedRule)
								.map((rule, i) => {
									return (
										<div key={i} style={{ border: 'black 2px solid' }} className="p-2">
											<div>
												<label htmlFor="mandatory-tags[]">Mandatory tags (optionnel) : </label>
												<input
													type="text"
													id="mandatory-tags[]"
													name="mandatory-tags[]"
													placeholder="Ex: very_small_company no_gender smcp"
													value={rule.mandatory_tags.join(' ')}
													onChange={(e) => {
														rule.mandatory_tags = e.target.value !== '' ? e.target.value.split(' ') : [];
														setRules([...rules]); // to force rerender
													}}
												/>
												<p>
													<strong>Description :</strong>{' '}
													<span id="mandatory-tags-description[]">
														Tags que l'évaluation doit posséder pour déclencher cette règle (tous). Tags séparés par des espaces.
													</span>
												</p>
											</div>

											<div>
												<label htmlFor="forbidden-tags[]">Forbidden tags (optionnel) : </label>
												<input
													type="text"
													id="forbidden-tags[]"
													name="forbidden-tags[]"
													placeholder="Ex: very_small_company no_gender smcp"
													value={rule.forbidden_tags.join(' ')}
													onChange={(e) => {
														rule.forbidden_tags = e.target.value !== '' ? e.target.value.split(' ') : [];
														setRules([...rules]); // to force rerender
													}}
												/>
												<p>
													<strong>Description :</strong>{' '}
													<span id="forbidden-tags-description[]">
														Tags que l'évaluation ne doit pas posséder pour déclencher cette règle (aucun). Tags séparés par des
														espaces.
													</span>
												</p>
											</div>
											<div style={{ display: attributionMode === 'range' ? '' : 'none' }}>
												<label htmlFor="range2[]">Intervalles de choix : </label>
												<input
													type="text"
													id="range2[]"
													name="range2[]"
													placeholder="Ex: 10 20 30 40"
													value={rule.rule || ''}
													onChange={(e) => {
														rule.rule = e.target.value;
														setRules([...rules]); // to force rerender
													}}
												/>
												<p>
													<strong>Description :</strong>{' '}
													<span id="range2-description[]">
														Selon la valeur obtenue par la réponse (brute ou calculée selon les critères), on attribue des choix.
														Séparez vos intervalles avec des espaces. Ex: <strong>10 20 30 40</strong>. Si la valeur de réponse est
														inférieure à 10, le choix 1 sera choisi. Si inférieure à 20, ce sera le choix 2, ... Les valeurs doivent
														être croissantes. Elles peuvent être négatives.
													</span>
												</p>
											</div>
										</div>
									);
								})}
							<p>
								<strong>Information :</strong>{' '}
								<span>
									Pour les règles d'attributions conditionnelles, la première règle qui est en accord avec les tags d'évaluation sera choisie.
									Les cas spécifiques doivent donc en théorie être placés en premier.
								</span>
							</p>
						</div>
					</div>
				</div>
				<div className="col-lg-6 col-12 d-flex flex-column">
					<span>Résultat :</span>
					{isUnknown ? (
						<span className="color--red">
							<i className="fa fa-exclamation-circle"></i> Type inconnu. Vérifiez que tout est correct car cela risque de ne pas fonctionner.
						</span>
					) : (
						''
					)}
					<textarea id="result" style={{ height: '500px' }} value={generateResult()}></textarea>
				</div>
			</div>
		</section>
	);
}

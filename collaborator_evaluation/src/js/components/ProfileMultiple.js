import React, { useState, useEffect, useRef } from 'react';
import './ProfileMultiple.css';

export default function ProfileMultiple(props) {
	function renderFormValues(form) {
		return form.values.map((value, i) => {
			return (
				<label data-ismultiple="true" className="checkbox-wrapper w-100">
					<a
						data-ismultiple="true"
						className="checkbox profile-form-dropdown-value d-flex justify-content-between align-items-center gap-2"
						key={'value' + i}
					>
						<input
							className="checkbox__trigger visuallyhidden"
							data-valuenames={JSON.stringify(value)}
							checked={isChecked(value[0])}
							type="checkbox"
							data-id={value[0]}
							id={'profile_checkbox_' + value[0]}
							onChange={(el) => {
								checkAnswer(el);
							}}
						/>
						<span data-ismultiple="true" className="checkbox__symbol">
							<svg
								data-ismultiple="true"
								aria-hidden="true"
								className="icon-checkbox"
								width="28px"
								height="28px"
								viewBox="0 0 28 28"
								version="1"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path d="M4 14l8 7L24 7"></path>
							</svg>
						</span>
						<span data-ismultiple="true" className="w-100 checkbox__textwrapper" data-valuenames={JSON.stringify(value)}>
							{value[1]}
							{i === 0 && <i className="fa fa-chevron-down dropdown-value-icon"></i>}
						</span>
					</a>
				</label>
			);
		});
	}

	function checkAnswer(el) {
		const target = el.target;
		if (!props.answerRef.current[props.answerId]) {
			props.answerRef.current[props.answerId] = [];
		}
		let data = JSON.parse(target.getAttribute('data-valuenames'));
		if (!target.checked) {
			props.answerRef.current[props.answerId].forEach((element, index) => {
				if (element[0] === data[0]) {
					props.answerRef.current[props.answerId].splice(index, 1);
				}
			});
		} else {
			props.answerRef.current[props.answerId].push(data);
		}
		if (props.answerRef.current[props.answerId].length === 0) {
			delete props.answerRef.current[props.answerId];
		}
		props.handleInputs();
	}

	function isChecked(id) {
		const elem = props.answerRef.current[props.answerId];
		if (elem) {
			for (let i = 0; i < elem.length; i++) {
				if (elem[i][0] === id) {
					return true;
				}
			}
		}
		return false;
	}

	function getLabel() {
		const elem = props.answerRef.current[props.answerId];
		return (elem && elem.map((e) => e[1]).join(', ')) || gettext('Veuillez cocher au moins une case');
	}

	return (
		<div className="profile-form-dropdown ">
			<button
				onClick={() => {
					props.toggleList(props.id);
				}}
				className="profile-form-dropbtn button button--circle"
			>
				<span className="profile-multiple-label">{getLabel()}</span>
				<i className="fa fa-chevron-right"></i>
			</button>
			<div
				className="profile-form-dropdown-content"
				style={{
					border: props.isOpened ? '' : 'none',
				}}
			>
				{props.isOpened && renderFormValues(props.form)}
			</div>
		</div>
	);
}

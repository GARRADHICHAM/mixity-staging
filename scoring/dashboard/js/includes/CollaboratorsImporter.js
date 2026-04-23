import React from 'react';
import { Modal } from 'react-bootstrap';

class CollaboratorsImporter extends React.Component {
	constructor(props) {
		super(props);
		this.fileInputRef = React.createRef();
		this.state = {
			//related to /api/url/ request
			emptyurl: '',
			url: '',
			urlEvaluation: '',
			synthesis: {},

			//var
			showModal: false,
			modalMessage: '',
		};
	}

	handleFileInputChange = (event) => {
		const file = event.target.files[0];
		if (file) {
			this.readFile(file);
		}
	};

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return {
					showModal: true,
					modalMessage: response.body,
				};
			});
		}
		return;
	}

	async fetchCSVHandler(file) {
		const response_url = await fetch('api/url/');
		this.fetchErrorMessage(response_url);
		const data_url = await response_url.json();

		let url = 'https://' + data_url;
		let emptyurl = url;
		let url_evaluation = 'https://' + data_url;
		if (window.location.pathname.split('/').filter(Boolean)[0])
			url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/' + window.location.pathname.split('/').filter(Boolean)[1];
		const is_diag_page = window.location.href.includes('diag');
		this.setState(() => {
			return {
				emptyurl: emptyurl,
				url: url,
				urlEvaluation: url_evaluation,
				isDiagPage: is_diag_page,
			};
		});
		const formData = new FormData();
		formData.append('file', file);
		fetch(this.state.url + '/api/' + this.props.evaluation_pk + '/handle-collaborators-list/', {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({ file_content: file }),
		})
			.then((response) => response.json())
			.then((data) => {
				this.setState(() => {
					return {
						showModal: true,
						modalMessage: data,
					};
				});
			});
		if (this.props.onSuccess) {
			this.props.onSuccess();
		}
	}

	readFile = (file) => {
		const reader = new FileReader();
		reader.onload = (e) => {
			const content = e.target.result;
			this.fetchCSVHandler(content);
		};
		reader.readAsText(file, 'UTF-8');
	};

	handleButtonClick = () => {
		this.fileInputRef.current.click();
	};

	render() {
		return (
			<>
				<input type="file" accept=".csv" style={{ display: 'none' }} ref={this.fileInputRef} onChange={this.handleFileInputChange} />
				<button className={this.props.className} style={this.props.style} onClick={this.handleButtonClick}>
					<i className={this.props.logo_style}></i>
					{this.props.text}
				</button>
				<Modal
					show={this.state.showModal && this.props.needModal}
					onHide={() => this.setState({ showModal: false })}
					aria-labelledby="contained-modal-title-vcenter"
					size={'m'}
					style={{ zIndex: '1050' }}
					className="criteria_modal m-0 p-0"
					centered
				>
					<Modal.Body style={{ textAlign: 'center' }}>{this.state.modalMessage}</Modal.Body>
				</Modal>
			</>
		);
	}
}

export default CollaboratorsImporter;

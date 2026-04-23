const email = document.getElementById('crisp-script').getAttribute('data-email');
const user_name = document.getElementById('crisp-script').getAttribute('data-username');
const crisp_id = document.getElementById('crisp-script').getAttribute('data-crispid');

import { Crisp } from 'crisp-sdk-web';

Crisp.configure(crisp_id);

if (email) {
	Crisp.user.setEmail(email);
}
if (user_name) {
	Crisp.user.setNickname(user_name);
}

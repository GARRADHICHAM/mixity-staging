import os
from unittest import mock

# La bibliothèque cloudinary_storage lit ses identifiants dès l'import : faux identifiants pour les tests.
os.environ.setdefault("CLOUDINARY_URL", "cloudinary://key:secret@mixity")

import cloudinary  # noqa: E402
from django.test import SimpleTestCase  # noqa: E402

from mixity.storage import FlatCloudinaryStorage  # noqa: E402


class FlatCloudinaryStorageTest(SimpleTestCase):
    def setUp(self):
        cloudinary.config(cloud_name="mixity", api_key="x", api_secret="x", secure=True)
        self.storage = FlatCloudinaryStorage()

    def test_url_ignores_folder_stored_in_database(self):
        url = self.storage.url("media/logos/societe_logo_cpysda")
        self.assertTrue(url.startswith("https://res.cloudinary.com/mixity/image/upload/"))
        self.assertTrue(url.endswith("/societe_logo_cpysda"))
        self.assertNotIn("media/logos", url)

    def test_url_is_the_same_with_or_without_folder(self):
        self.assertEqual(
            self.storage.url("media/logos/societe_logo_cpysda"),
            self.storage.url("societe_logo_cpysda"),
        )

    def test_url_keeps_accents(self):
        url = self.storage.url("media/logos/Logo_Crédit_Coopératif_svg_1_bkffdk")
        self.assertNotIn("media/logos", url)
        self.assertIn("Cr", url)

    def test_upload_sends_folder_as_asset_folder_only(self):
        with mock.patch("cloudinary.uploader.upload", return_value={"public_id": "x"}) as upload:
            self.storage._upload("media/logos/x.png", object())
        options = upload.call_args.kwargs
        self.assertEqual(options["asset_folder"], "media/logos")
        self.assertNotIn("folder", options)
        self.assertTrue(options["use_filename"])

    def test_upload_without_folder_has_no_asset_folder(self):
        with mock.patch("cloudinary.uploader.upload", return_value={"public_id": "x"}) as upload:
            self.storage._upload("x.png", object())
        self.assertNotIn("asset_folder", upload.call_args.kwargs)

    def test_delete_uses_file_name_only(self):
        with mock.patch("cloudinary.uploader.destroy", return_value={"result": "ok"}) as destroy:
            self.assertTrue(self.storage.delete("media/logos/x_abc"))
        self.assertEqual(destroy.call_args.args[0], "x_abc")


class FlatRawCloudinaryStorageTest(SimpleTestCase):
    def setUp(self):
        cloudinary.config(cloud_name="mixity", api_key="x", api_secret="x", secure=True)
        from mixity.storage import FlatRawCloudinaryStorage

        self.storage = FlatRawCloudinaryStorage()

    def test_excel_url_is_raw_without_folder(self):
        url = self.storage.url("media/questions_sheets/questionnaire_yalkgl.xlsx")
        self.assertEqual(
            url, "https://res.cloudinary.com/mixity/raw/upload/questionnaire_yalkgl.xlsx"
        )

    def test_csv_url_is_raw_without_folder(self):
        url = self.storage.url("media/name_data/export_abc.csv")
        self.assertEqual(url, "https://res.cloudinary.com/mixity/raw/upload/export_abc.csv")

    def test_pdf_is_served_as_image(self):
        url = self.storage.url("media/pdf_sheets/pdf_mfrd63.pdf")
        self.assertTrue(url.startswith("https://res.cloudinary.com/mixity/image/upload/"))
        self.assertTrue(url.endswith("/pdf_mfrd63.pdf"))
        self.assertNotIn("pdf_sheets", url)

    def test_upload_keeps_resource_type(self):
        with mock.patch("cloudinary.uploader.upload", return_value={"public_id": "x"}) as upload:
            self.storage._upload("media/sheets/export.xlsx", object())
        self.assertEqual(upload.call_args.kwargs["resource_type"], "raw")
        self.assertEqual(upload.call_args.kwargs["asset_folder"], "media/sheets")

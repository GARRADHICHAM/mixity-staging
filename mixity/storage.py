import os

import cloudinary
import cloudinary.uploader
from cloudinary_storage.storage import RESOURCE_TYPES, MediaCloudinaryStorage


class FlatCloudinaryStorage(MediaCloudinaryStorage):
    """
    Stockage pour un compte Cloudinary en "dynamic folders".

    Dans ce mode, l'identifiant public d'un fichier est son nom seul : le dossier
    n'est qu'un rangement dans la médiathèque et ne fait plus partie de l'URL.
    Les noms enregistrés en base peuvent encore contenir un dossier
    ("media/logos/fichier_abc"), on ne garde donc que le nom du fichier.
    """

    def _upload(self, name, content):
        options = {
            "use_filename": True,
            "resource_type": self._get_resource_type(name),
            "tags": self.TAG,
        }
        folder = os.path.dirname(name)
        if folder:
            options["asset_folder"] = folder
        return cloudinary.uploader.upload(content, **options)

    def _get_url(self, name):
        public_id = os.path.basename(name)
        resource = cloudinary.CloudinaryResource(
            public_id, default_resource_type=self._get_resource_type(public_id)
        )
        return resource.url

    def delete(self, name):
        public_id = os.path.basename(name)
        response = cloudinary.uploader.destroy(
            public_id,
            invalidate=True,
            resource_type=self._get_resource_type(public_id),
        )
        return response["result"] == "ok"


class FlatRawCloudinaryStorage(FlatCloudinaryStorage):
    """
    Même stockage pour les fichiers bruts (Excel, CSV).

    Les PDF sont rangés comme des images sur le compte Cloudinary : ils restent
    servis par "image/upload" (la diffusion des PDF doit être autorisée dans
    les réglages de sécurité du compte).
    """

    RESOURCE_TYPE = RESOURCE_TYPES["RAW"]

    def _get_resource_type(self, name):
        if name.lower().endswith(".pdf"):
            return RESOURCE_TYPES["IMAGE"]
        return self.RESOURCE_TYPE

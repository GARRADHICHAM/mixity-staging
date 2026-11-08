import os

import cloudinary
from django.core.files.storage import FileSystemStorage


class LocalOrCloudinaryStorage(FileSystemStorage):
    """
    Stockage de développement (sans clés Cloudinary).

    Les fichiers sont enregistrés sur le disque. Pour l'affichage, un fichier absent
    du disque (cas de la base copiée depuis la production) est lu sur Cloudinary,
    avec la même adresse que celle construite en production (mixity.storage).
    """

    RESOURCE_TYPE = "image"

    def url(self, name):
        if not name or not cloudinary.config().cloud_name or self.exists(name):
            return super().url(name)
        public_id = os.path.basename(name)
        resource_type = "image" if public_id.lower().endswith(".pdf") else self.RESOURCE_TYPE
        return cloudinary.CloudinaryResource(
            public_id, default_resource_type=resource_type
        ).url


class LocalOrCloudinaryRawStorage(LocalOrCloudinaryStorage):
    RESOURCE_TYPE = "raw"

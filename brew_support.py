import sys
import io
import tarfile
import json
import logging

from google.appengine.api import urlfetch

from hashlib import sha256

class HomebrewPkg:
    def __init__(self, brew_pkg):
        self.id = brew_pkg
        self.formula_url = "https://formulae.brew.sh/api/formula/{}.json".format(self.id)
        self.formula_data = None
        self.name = None
        self.description = None
        self.src_url = None
        self.current_version = None
        self.short_version = None
        self.other_versions = None
        self.pkg_url = {"catalina": None, "mojave": None}
        self.hashes = {"catalina": None, "mojave": None}
        self.get_pkg()

    def handle_error(self, req):
        if req.status_code == 404:
            print("Error: formula not found for '{}' (url:{})".format(
                self.id,
                self.formula_url))
        else:
            print("Error: received status {} from server when fetching {}".format(
                req.status_code,
                self.formula_url))
        raise Exception

    def get_pkg(self):
        try:
            r = urlfetch.fetch(self.formula_url)
            if r.status_code == 200:
                self.formula_data = json.loads(r.content)
                self.extract_metadata()
                self.extract_hash()
            else:
                self.handler_error(r)
        except urlfetch.Error:
            logging.exception("Caught exception when fetching url")



    def extract_metadata(self):
        if "@" in self.formula_data["name"]:
            self.name = self.formula_data["name"].split("@")[0]
        else:
            self.name = self.formula_data["name"]
        self.description = self.formula_data["desc"]
        self.src_url = self.formula_data["urls"]["stable"]["url"]
        self.current_version = self.formula_data["versions"]["stable"]
        self.other_versions = [x.split("@")[1] for x in self.formula_data["versioned_formulae"]]
        self.extract_urls()

    def extract_urls(self):
        pkg_files = self.formula_data["bottle"]["stable"]["files"]
        self.pkg_url["catalina"] = pkg_files["catalina"]["url"]
        self.pkg_url["mojave"] = pkg_files["mojave"]["url"]

    def info(self):
        print("Name: {}".format(self.name))
        print("Description: {}".format(self.description))
        print("Source: {}".format(self.src_url))
        print("Version: {}".format(self.current_version))
        print("Other versions: {}".format(self.other_versions))
        for version in self.hashes:
            if self.hashes[version]:
                print("SHA256 [{}]: {}".format(version, self.hashes[version]))

    def extract_hash(self):
        path = "{pkg_id}/{version}/bin/{name}".format(
                pkg_id=self.id,
                version=self.current_version,
                name=self.name)
        for version in self.pkg_url:
            if self.pkg_url[version]:
                try:
                    r = urlfetch.fetch(self.pkg_url[version])
                    if r.status_code == 200:
                        tf = tarfile.open(fileobj=io.BytesIO(r.content), mode="r")
                        if tf:
                            file_data = tf.extractfile(path)
                            self.hashes[version] = sha256(file_data.read()).hexdigest()
                        else:
                            print("Unable to extract file: {}".format(path))
                    else:
                        self.handle_error(r)
                except urlfetch.Error:
                    logging.exception("Caught exception when fetching URL")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: {} <brew-pkg>".format(sys.argv[0]))
        exit()
    try:
        pkg = HomebrewPkg(sys.argv[1])
    except Exception as e:
        pass
    else:
        pkg.info()


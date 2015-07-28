from fabric.operations import _AttributeString
from alarmageddon.validations.validation import Validation
import time


def get_mock_key_file(tmpdir):
    tmp_file = tmpdir.join("secret.pem")
    tmp_file.write('secret')
    return tmp_file.strpath


def get_mock_ssh_text(text, code):
    result = _AttributeString(text)
    result.return_code = code
    return result

class NeverFinish(Validation):
    #don't actually never finish, that would be bad if we don't handle it well
    def perform(self, group_failures):
        time.sleep(60)

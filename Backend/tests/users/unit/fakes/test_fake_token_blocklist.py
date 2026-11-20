import uuid

import pytest

from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.domain.value_objects.user_id import UserId
from tests.users.contracts.token_blocklist_contract import TokenBlocklistContract
from tests.users.fakes.fake_token_blocklist import FakeTokenBlocklist


class TestFakeTokenBlocklist(TokenBlocklistContract):
    @pytest.fixture
    def blocklist(self) -> TokenBlocklist:
        return FakeTokenBlocklist()

    @pytest.fixture
    def usuario(self) -> UserId:
        return UserId(uuid.uuid4())

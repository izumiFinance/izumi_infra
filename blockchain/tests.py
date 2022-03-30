# -*- coding: utf-8 -*-
import json
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from izumi_infra.blockchain.context import blockchainHolder
from izumi_infra.blockchain.models import Blockchain, Contract

# Create your tests here.
class BlockchainTests(TestCase):
    fixtures = ['fixtures/test/blockchain.json']

    def setUp(self):
        blockchain_model = Blockchain.objects.first()
        self.blockchain_facade = blockchainHolder.get_facade_by_model(blockchain_model)

    def testIsConnect(self):
        self.assertTrue(self.blockchain_facade.is_connected())

    def testLatestBlock(self):
        self.assertNotEqual(self.blockchain_facade.get_lastest_block_number(), 0)

    def testConextGet(self):
        blockchain_model = Blockchain.objects.first()
        blockchainHolder.get_facade_by_model(blockchain_model)
        first = blockchainHolder.get_context_size()
        blockchainHolder.get_facade_by_model(blockchain_model)
        self.assertEqual(blockchainHolder.get_context_size(), first)

class ModelEnumTest(TestCase):
    fixtures = ['fixtures/test/blockchain.json', 'fixtures/test/contract.json']

class BlockchainApiTest(TestCase):
    fixtures = ['fixtures/test/blockchain.json', 'fixtures/test/contract.json', 'fixtures/test/bridgescantask.json']

    def setUp(self) -> None:
        self.client = APIClient(enforce_csrf_checks=True)

    def testContractViewList(self):
        url = '/api/v1/blockchain/contract/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json.loads(response.content)
        self.assertTrue(result['is_success'])
        result_data = result['data']
        self.assertGreater(len(result_data), 0)
        self.assertGreater(len(result_data[0]['tokens']), 0)

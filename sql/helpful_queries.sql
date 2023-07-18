-- Some few queries

-- Balances
SELECT * FROM balances
WHERE token_address = LOWER('0x600000000a36f3cd48407e35eb7c5c910dc1f7a8')
ORDER BY balance DESC;

-- Transfers
SELECT * FROM transfers
ORDER BY block_num DESC;

SELECT COUNT(*) FROM transfers
WHERE token_address = LOWER('0xBAac2B4491727D78D2b78815144570b9f2Fe8899')
AND value > 0;

SELECT * FROM transfers
WHERE token_address = LOWER('0x600000000a36f3cd48407e35eb7c5c910dc1f7a8')
ORDER BY block_num DESC;
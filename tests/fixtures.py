"""Test fixtures for Solana swarm"""

# Mock vulnerable contract
VULNERABLE_CONTRACT = """
#[program]
pub mod vulnerable_contract {
    use anchor_lang::prelude::*;

    #[account]
    pub struct Vault {
        pub balance: u64,
        pub owner: Pubkey,
    }

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        // VULNERABILITY: No overflow check!
        ctx.accounts.vault.balance -= amount;

        // Transfer SOL
        anchor_lang::system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                anchor_lang::system_program::Transfer {
                    from: ctx.accounts.user.to_account_info(),
                    to: ctx.accounts.vault.to_account_info(),
                },
            ),
            amount,
        )?;

        Ok(())
    }

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        // VULNERABILITY: No access control check!
        let vault = &mut ctx.accounts.vault;
        vault.owner = ctx.accounts.user.key();
        vault.balance = 0;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = user, space = 8 + 8 + 32)]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}
"""

# Mock wallet positions
MOCK_WALLET = {
    "address": "So11111111111111111111111111111111111111112",
    "positions": {
        "SOL": 100,
        "USDC": 50000,
        "mSOL": 80,
    },
}

# Mock contract address
MOCK_CONTRACT_ADDRESS = "11111111111111111111111111111111"

# Test scenarios
SCENARIOS = {
    "audit_only": {
        "user_input": "Audit this smart contract for vulnerabilities",
        "contract_code": VULNERABLE_CONTRACT,
        "contract_address": MOCK_CONTRACT_ADDRESS,
    },
    "defi_only": {
        "user_input": "Analyze my wallet and suggest yield opportunities",
        "wallet_address": MOCK_WALLET["address"],
        "positions": MOCK_WALLET["positions"],
    },
    "combined": {
        "user_input": "Audit my contract and optimize my DeFi yields",
        "contract_code": VULNERABLE_CONTRACT,
        "contract_address": MOCK_CONTRACT_ADDRESS,
        "wallet_address": MOCK_WALLET["address"],
        "positions": MOCK_WALLET["positions"],
    },
}

#![no_std]

use soroban_sdk::{
    contract, contractimpl, contracterror, contracttype, Address, Env, String,
};

#[derive(Debug)]
#[contracttype]
pub enum DataKey {
    Admin,
    NextTokenId,
    Owner(u128),
    Metadata(u128),
}

#[derive(Clone)]
#[contracttype]
pub struct ProjectMetadata {
    pub project_id: String,
    pub ipfs_cid: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
#[contracterror]  // <-- ÖNEMLİ: Error artık contract error
pub enum Error {
    AlreadyInitialized = 1,
    NotInitialized = 2,
    NotAdmin = 3,
    TokenNotFound = 4,
    NotTokenOwner = 5,
}

fn read_admin(env: &Env) -> Result<Address, Error> {
    let store = env.storage().persistent();
    if let Some(admin) = store.get::<_, Address>(&DataKey::Admin) {
        Ok(admin)
    } else {
        Err(Error::NotInitialized)
    }
}

fn write_admin(env: &Env, admin: &Address) {
    let store = env.storage().persistent();
    store.set(&DataKey::Admin, admin);
}

fn read_next_token_id(env: &Env) -> u128 {
    let store = env.storage().persistent();
    store
        .get::<_, u128>(&DataKey::NextTokenId)
        .unwrap_or(1u128) // ilk token_id = 1
}

fn write_next_token_id(env: &Env, id: u128) {
    let store = env.storage().persistent();
    store.set(&DataKey::NextTokenId, &id);
}

fn read_owner(env: &Env, token_id: u128) -> Option<Address> {
    let store = env.storage().persistent();
    store.get::<_, Address>(&DataKey::Owner(token_id))
}

fn write_owner(env: &Env, token_id: u128, owner: &Address) {
    let store = env.storage().persistent();
    store.set(&DataKey::Owner(token_id), owner);
}

fn remove_owner(env: &Env, token_id: u128) {
    let store = env.storage().persistent();
    store.remove(&DataKey::Owner(token_id));
}

fn read_metadata(env: &Env, token_id: u128) -> Option<ProjectMetadata> {
    let store = env.storage().persistent();
    store.get::<_, ProjectMetadata>(&DataKey::Metadata(token_id))
}

fn write_metadata(env: &Env, token_id: u128, meta: &ProjectMetadata) {
    let store = env.storage().persistent();
    store.set(&DataKey::Metadata(token_id), meta);
}

#[contract]
pub struct ProjectNft;

#[contractimpl]
impl ProjectNft {
    /// Kontratı başlatır. Sadece bir kere çağrılabilir.
    pub fn init(env: Env, admin: Address) -> Result<(), Error> {
        let store = env.storage().persistent();
        if store.has(&DataKey::Admin) {
            return Err(Error::AlreadyInitialized);
        }

        // deploy eden adres gerçekten admin olsun
        admin.require_auth();

        write_admin(&env, &admin);
        write_next_token_id(&env, 1u128);

        Ok(())
    }

    /// Yeni bir proje token'ı mint eder.
    /// Sadece admin çağırabilir.
    pub fn mint(
        env: Env,
        to: Address,
        project_id: String,
        ipfs_cid: String,
    ) -> Result<u128, Error> {
        let admin = read_admin(&env)?;

        // sadece admin mint edebilir
        admin.require_auth();

        let token_id = read_next_token_id(&env);

        let meta = ProjectMetadata {
            project_id,
            ipfs_cid,
        };

        write_owner(&env, token_id, &to);
        write_metadata(&env, token_id, &meta);

        write_next_token_id(&env, token_id + 1);

        Ok(token_id)
    }

    /// Token transferi.
    pub fn transfer(env: Env, from: Address, to: Address, token_id: u128) -> Result<(), Error> {
        let owner = read_owner(&env, token_id).ok_or(Error::TokenNotFound)?;

        from.require_auth();
        if from != owner {
            return Err(Error::NotTokenOwner);
        }

        write_owner(&env, token_id, &to);
        Ok(())
    }

    /// Token sahibini döner.
    pub fn owner_of(env: Env, token_id: u128) -> Result<Address, Error> {
        read_owner(&env, token_id).ok_or(Error::TokenNotFound)
    }

    /// Token metadata'sını döner.
    pub fn get_metadata(env: Env, token_id: u128) -> Result<ProjectMetadata, Error> {
        read_metadata(&env, token_id).ok_or(Error::TokenNotFound)
    }

    /// Basit versiyon fonksiyonu
    pub fn version(env: Env) -> String {
        // SDK 23.2.1: from_str(&Env, &str)
        String::from_str(&env, "project-nft v1")
    }
}

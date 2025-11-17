ALTER TABLE events
    ADD CONSTRAINT events_provider_msg_id_unique UNIQUE (provider_msg_id);
